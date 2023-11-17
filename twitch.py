# reading twitch chat w/ socket: https://www.learndatasci.com/tutorials/how-stream-text-data-twitch-sockets-python/

import re
import socket

from common.rabbitmq import AWSRabbitMQClient
import settings


rabbit = AWSRabbitMQClient(settings.AMQP_URL)
rabbit.declare_queue(settings.TWITCH_AMQP_QUEUE)

server = 'irc.chat.twitch.tv'
port = 6667


sock = socket.socket()
sock.connect((server, port))

sock.send(f"PASS {settings.TWITCH_OAUTH_TOKEN}\n".encode('utf-8'))
sock.send(f"NICK {settings.TWITCH_NICKNAME}\n".encode('utf-8'))
sock.send(f"JOIN {settings.TWITCH_CHANNEL}\n".encode('utf-8'))

while True:
    resp = sock.recv(2048).decode('utf-8')

    if resp.startswith('PING'):
        sock.send("PONG\n".encode('utf-8'))

    elif len(resp) > 0:
        if 'PRIVMSG' in resp:
            username, channel, message = re.search(':(.*)\!.*@.*\.tmi\.twitch\.tv PRIVMSG #(.*) :(.*)', resp).groups()
            message = message.strip()

            print(f"Channel: {channel} \nUsername: {username} \nMessage: {message}")
            rabbit.send_message(exchange="", routing_key=settings.TWITCH_AMQP_QUEUE, body=bytes(username + '#' + message, 'utf-8'))
