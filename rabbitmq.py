# Various bits taken from https://docs.aws.amazon.com/amazon-mq/latest/developer-guide/amazon-mq-rabbitmq-pika.html

import pika
import ssl


class AWSRabbitMQClient:
    def __init__(self, url):
        self.connection = None
        self.channel = None
        self.url = url
        # SSL Context for TLS configuration of Amazon MQ for RabbitMQ
        self.setup_connection()

    def setup_connection(self):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        ssl_context.set_ciphers('ECDHE+AESGCM:!ECDSA')

        parameters = pika.URLParameters(self.url)
        parameters.ssl_options = pika.SSLOptions(context=ssl_context)
        parameters.heartbeat = 30
        parameters.blocked_connection_timeout = 60
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

    def declare_queue(self, queue_name):
        print(f"Declaring queue {queue_name}")
        self.channel.queue_declare(queue=queue_name)

    def send_message(self, exchange, routing_key, body):
        # TODO: remove try/except after adding mq heartbeat
        try:
            channel = self.connection.channel()
        except:
            self.setup_connection()
            channel = self.connection.channel()

        channel.basic_publish(exchange=exchange,
                              routing_key=routing_key,
                              body=body)
        print(f"Sent message. Exchange: {exchange}, Routing Key: {routing_key}, Body: {body}")

    def get_message(self, queue):
        method_frame, header_frame, body = self.channel.basic_get(queue)
        if method_frame:
            print(method_frame, header_frame, body)
            self.channel.basic_ack(method_frame.delivery_tag)
            return method_frame, header_frame, body
        else:
            print('No message returned')
            return None

    def close(self):
        self.channel.close()
        self.connection.close()
