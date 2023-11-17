from common.gamepad import SwitchController
from common.rabbitmq import AWSRabbitMQClient
import settings


def process(ch, method, properties, body):
    decoded_body = body.decode()
    username = decoded_body.split('#')[0]
    message = decoded_body.split('#')[-1].lower()
    print(f"Received decoded body: {decoded_body}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

    if ':' in message:
        try:
            input = message.split(':')[0]
            modifier = message.split(':')[1]
        except ValueError:
            return
    else:
        input = message
        modifier = None

    if input in gamepad.input_to_queue_map.keys():
        gamepad.enqueue_input(input, modifier, username)
    else:
        print(f'{username}: No idea what to do with: {message}')


gamepad = SwitchController()


if __name__ == '__main__':
    rabbit = AWSRabbitMQClient(settings.AMQP_URL)
    rabbit.declare_queue(settings.TWITCH_AMQP_QUEUE)

    rabbit.channel.basic_qos(prefetch_count=1)
    rabbit.channel.basic_consume(queue=settings.TWITCH_AMQP_QUEUE, on_message_callback=process)

    gamepad.listen()

    rabbit.channel.start_consuming()

    del gamepad
