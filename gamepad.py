# vgamepad dualshock4 docs and examples: https://github.com/yannbouteiller/vgamepad#dualshock4-gamepad

from time import sleep

import vgamepad as vg

from rabbitmq import AWSRabbitMQClient
import settings


rabbit = AWSRabbitMQClient(settings.AMQP_URL)
rabbit.declare_queue(settings.TWITCH_AMQP_QUEUE)
gamepad = vg.VDS4Gamepad()


MESSAGE_TO_INPUT_MAP = {
    'buttons': {
        'start': vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS,
        'select': vg.DS4_BUTTONS.DS4_BUTTON_SHARE,
        'triangle': vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE,
        'square': vg.DS4_BUTTONS.DS4_BUTTON_SQUARE,
        'cross': vg.DS4_BUTTONS.DS4_BUTTON_CROSS,
        'circle': vg.DS4_BUTTONS.DS4_BUTTON_CIRCLE,
        'r1': vg.DS4_BUTTONS.DS4_BUTTON_TRIGGER_RIGHT,
        'r2': vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT,
        'r3': vg.DS4_BUTTONS.DS4_BUTTON_THUMB_RIGHT,
        'l1': vg.DS4_BUTTONS.DS4_BUTTON_TRIGGER_LEFT,
        'l2': vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT,
        'l3': vg.DS4_BUTTONS.DS4_BUTTON_THUMB_LEFT,
    },
    'directions': {
        'up': vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTH,
        'down': vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTH,
        'left': vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_WEST,
        'right': vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_EAST,
    }
}


def process(ch, method, properties, body):
    message = body.decode()
    print(f"Received decoded body: {message}")
    ch.basic_ack(delivery_tag=method.delivery_tag)
    if message.lower() in MESSAGE_TO_INPUT_MAP['buttons']:
        gamepad.press_button(button=MESSAGE_TO_INPUT_MAP['buttons'][message])
        gamepad.update()
        sleep(.5)
        gamepad.release_button(button=MESSAGE_TO_INPUT_MAP['buttons'][message])
        gamepad.update()
        print(f"Pressed and released {MESSAGE_TO_INPUT_MAP['buttons'][message]}")
    elif message.lower() in MESSAGE_TO_INPUT_MAP['directions']:
        gamepad.directional_pad(direction=MESSAGE_TO_INPUT_MAP['directions'][message])
        gamepad.update()
        sleep(.5)
        gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE)
        gamepad.update()
        print(f"Pressed and released {MESSAGE_TO_INPUT_MAP['directions'][message]}")


rabbit.channel.basic_qos(prefetch_count=1)
rabbit.channel.basic_consume(queue=settings.TWITCH_AMQP_QUEUE, on_message_callback=process)

rabbit.channel.start_consuming()
