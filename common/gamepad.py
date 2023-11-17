# vgamepad dualshock4 docs and examples: https://github.com/yannbouteiller/vgamepad#dualshock4-gamepad
import queue
import threading
from time import sleep, time

import redis
import vgamepad as vg


class BaseGamepadManager(threading.Thread):
    def __init__(self, gamepad, display_name, *args, **kwargs):
        self.gamepad = gamepad
        self.display_name = display_name
        super().__init__(*args, **kwargs)

    def log_action(self, username, action, modifier):
        timestamp = str(time())
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.zadd('latest_commands', {f'{username}#{action}#{modifier}#{timestamp}': timestamp})
        r.quit()


class ButtonManager(BaseGamepadManager):
    def __init__(self, gamepad, display_name, queue, button, *args, **kwargs):
        self.queue = queue
        self.button = button
        super().__init__(gamepad, display_name, *args, **kwargs)

    def run(self):
        while True:
            message = self.queue.get(block=True)
            self.press_and_release_button(message)
            self.queue.task_done()

    def press_and_release_button(self, message):
        username = message.split('#')[0]
        modifier = message.split('#')[-1]
        if modifier == 'None':
            modifier = .05

        self.log_action(username, self.display_name, modifier)

        self.gamepad.press_button(button=self.button)
        self.gamepad.update()
        sleep(float(modifier))

        self.gamepad.release_button(button=self.button)
        self.gamepad.update()

        print(f"{username}: Pressed and released {self.button} for {modifier}s")


class DpadManager(BaseGamepadManager):
    def __init__(self, gamepad, display_name, up_queue, down_queue, left_queue, right_queue, *args, **kwargs):
        self.input_to_direction_map = {
            'up': vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTH,
            'down': vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTH,
            'left': vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_WEST,
            'right': vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_EAST
        }
        self.input_to_queue_map = {
            'up': up_queue,
            'down': down_queue,
            'left': left_queue,
            'right': right_queue
        }
        super().__init__(gamepad, display_name, *args, **kwargs)

    def run(self):
        while True:
            for direction, dpad_queue in self.input_to_queue_map.items():
                try:
                    message = dpad_queue.get(block=False)
                    self.press_and_release_dpad(direction, message)
                    dpad_queue.task_done()
                except queue.Empty:
                    sleep(.05)  # todo: this lowers cpu temp by 30c!!!
                    pass

    def press_and_release_dpad(self, direction, message):
        username = message.split('#')[0]
        modifier = message.split('#')[-1]
        if modifier == 'None':
            modifier = 1

        for i in range(int(modifier)):
            self.log_action(username, self.display_name + ' ' + direction, modifier)
            self.gamepad.directional_pad(direction=self.input_to_direction_map[direction])
            self.gamepad.update()
            sleep(.03)

            self.gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE)
            self.gamepad.update()
            sleep(.03)

        print(f"{username}: Pressed and released dpad {direction} x{modifier}")


class ThumbstickManager(BaseGamepadManager):
    def __init__(self, gamepad, display_name, up_queue, down_queue, left_queue, right_queue, thumbstick, *args, **kwargs):
        self.input_to_coordinates_map = {
            'up': (0.0, -1.0),
            'down': (0.0, 1.0),
            'left': (-1.0, 0.0),
            'right': (1.0, 0.0)
        }
        self.coordinates_to_input_map = {v: k for k, v in self.input_to_coordinates_map.items()}
        self.input_to_queue_map = {
            'up': up_queue,
            'down': down_queue,
            'left': left_queue,
            'right': right_queue
        }
        self.thumbstick = thumbstick
        super().__init__(gamepad, display_name, *args, **kwargs)

    def run(self):
        while True:
            for direction, thumbstick_queue in self.input_to_queue_map.items():
                try:
                    message = thumbstick_queue.get(block=False)
                    self.move_and_release_thumbstick(self.thumbstick, self.input_to_coordinates_map[direction], message)
                    thumbstick_queue.task_done()
                except queue.Empty:
                    sleep(.05)  # todo: same lol
                    pass

    def move_and_release_thumbstick(self, thumbstick, coordinates, message):
        username = message.split('#')[0]
        modifier = message.split('#')[-1]
        if self.thumbstick == 'left':
            self.gamepad.left_joystick_float(x_value_float=coordinates[0], y_value_float=coordinates[1])
        elif self.thumbstick == 'right':
            self.gamepad.right_joystick_float(x_value_float=coordinates[0], y_value_float=coordinates[1])
        self.gamepad.update()

        if modifier == 'None':
            modifier = .5

        direction = self.coordinates_to_input_map[coordinates]
        self.log_action(username, self.display_name + ' ' + direction, modifier)

        sleep(float(modifier))

        if self.thumbstick == 'left':
            self.gamepad.left_joystick_float(x_value_float=0.0, y_value_float=0.0)
        elif self.thumbstick == 'right':
            self.gamepad.right_joystick_float(x_value_float=0.0, y_value_float=0.0)
        self.gamepad.update()
        print(f"{username}: Moved and released {thumbstick} stick @ {coordinates} for {modifier}s")


class DualShockController(object):
    def __init__(self):
        self.gamepad = vg.VDS4Gamepad()

        self.select_queue = queue.Queue()
        self.start_queue = queue.Queue()

        self.triangle_queue = queue.Queue()
        self.circle_queue = queue.Queue()
        self.cross_queue = queue.Queue()
        self.square_queue = queue.Queue()
        self.l1_queue = queue.Queue()
        self.l2_queue = queue.Queue()
        self.r1_queue = queue.Queue()
        self.r2_queue = queue.Queue()

        self.dpad_up_queue = queue.Queue()
        self.dpad_down_queue = queue.Queue()
        self.dpad_left_queue = queue.Queue()
        self.dpad_right_queue = queue.Queue()

        self.thumbleft_up_queue = queue.Queue()
        self.thumbleft_down_queue = queue.Queue()
        self.thumbleft_left_queue = queue.Queue()
        self.thumbleft_right_queue = queue.Queue()

        self.input_to_queue_map = {
            'select': self.select_queue,
            'start': self.start_queue,
            'triangle': self.triangle_queue,
            'cross': self.cross_queue,
            'circle': self.circle_queue,
            'square': self.square_queue,
            'l1': self.l1_queue,
            'l2': self.l2_queue,
            'r1': self.r1_queue,
            'r2': self.r2_queue,
            'dup': self.dpad_up_queue,
            'ddown': self.dpad_down_queue,
            'dleft': self.dpad_left_queue,
            'dright': self.dpad_right_queue,
            'tlup': self.thumbleft_up_queue,
            'tldown': self.thumbleft_down_queue,
            'tlleft': self.thumbleft_left_queue,
            'tlright': self.thumbleft_right_queue,
        }

        self.select_processor = ButtonManager(
            gamepad=self.gamepad,
            display_name='select',
            queue=self.select_queue,
            button=vg.DS4_BUTTONS.DS4_BUTTON_SHARE
        )

        self.start_processor = ButtonManager(
            gamepad=self.gamepad,
            display_name='start',
            queue=self.start_queue,
            button=vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS
        )

        self.triangle_processor = ButtonManager(
            gamepad=self.gamepad,
            display_name='triangle',
            queue=self.triangle_queue,
            button=vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE
        )
        self.circle_processor = ButtonManager(
            gamepad=self.gamepad,
            display_name='circle',
            queue=self.circle_queue,
            button=vg.DS4_BUTTONS.DS4_BUTTON_CIRCLE
        )
        self.cross_processor = ButtonManager(
            gamepad=self.gamepad,
            display_name='cross',
            queue=self.cross_queue,
            button=vg.DS4_BUTTONS.DS4_BUTTON_CROSS
        )
        self.square_processor = ButtonManager(
            gamepad=self.gamepad,
            display_name='square',
            queue=self.square_queue,
            button=vg.DS4_BUTTONS.DS4_BUTTON_SQUARE
        )
        self.l1_processor = ButtonManager(
            gamepad=self.gamepad,
            display_name='l1',
            queue=self.l1_queue,
            button=vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT
        )
        self.l2_processor = ButtonManager(
            gamepad=self.gamepad,
            display_name='l2',
            queue=self.l2_queue,
            button=vg.DS4_BUTTONS.DS4_BUTTON_TRIGGER_LEFT
        )
        self.r1_processor = ButtonManager(
            gamepad=self.gamepad,
            display_name='r1',
            queue=self.r1_queue,
            button=vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT
        )
        self.r2_processor = ButtonManager(
            gamepad=self.gamepad,
            display_name='r2',
            queue=self.r2_queue,
            button=vg.DS4_BUTTONS.DS4_BUTTON_TRIGGER_RIGHT
        )

        self.dpad_processor = DpadManager(
            gamepad=self.gamepad,
            display_name='dpad',
            up_queue=self.dpad_up_queue,
            down_queue=self.dpad_down_queue,
            left_queue=self.dpad_left_queue,
            right_queue=self.dpad_right_queue
        )

        self.left_thumbstick_processor = ThumbstickManager(
            gamepad=self.gamepad,
            display_name='left thumbstick',
            up_queue=self.thumbleft_up_queue,
            down_queue=self.thumbleft_down_queue,
            left_queue=self.thumbleft_left_queue,
            right_queue=self.thumbleft_right_queue,
            thumbstick='left'
        )

        self.processors = [
            self.select_processor,
            self.start_processor,
            self.triangle_processor,
            self.circle_processor,
            self.cross_processor,
            self.square_processor,
            self.l1_processor,
            self.l2_processor,
            self.r1_processor,
            self.r2_processor,
            self.dpad_processor,
            self.left_thumbstick_processor
        ]

        super().__init__()

    def listen(self):
        for processor in self.processors:
            processor.start()

    def enqueue_input(self, input, modifier, username):
        try:
            if modifier and int(modifier) > 11:
                modifier = 10
        except:
            return

        self.input_to_queue_map[input].put(username + '#' + str(modifier))
