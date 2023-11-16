import settings
from common.gamepad import DualShockController
from common.rabbitmq import AWSRabbitMQClient


def process(ch, method, properties, body):
    message = body.decode().lower()
    print(f"Received decoded body: {message}")
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

    gamepad.enqueue_input(input, modifier)


gamepad = DualShockController()


if __name__ == '__main__':
    rabbit = AWSRabbitMQClient(settings.AMQP_URL)
    rabbit.declare_queue(settings.TWITCH_AMQP_QUEUE)

    rabbit.channel.basic_qos(prefetch_count=1)
    rabbit.channel.basic_consume(queue=settings.TWITCH_AMQP_QUEUE, on_message_callback=process)

    gamepad.listen()

    rabbit.channel.start_consuming()

    del gamepad
