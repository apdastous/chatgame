# HOWTO
* Set up rabbitmq
* Create settings.py and add the following:
  * AMQP_URL
  * TWITCH_NICKNAME
  * TWITCH_CHANNEL
  * TWITCH_OAUTH_TOKEN
  * TWITCH_AMQP_QUEUE

# TODO
* Threaded rabbitmq client
  * send proper heartbeats
  * aiopika?
* Multi-button inputs
* Dpad vs thumbstick
* Button hold duration
* Twitch chat schema for gamepad inputs
* Threaded (per button?) gamepad inputs
* Project structure
  * separate into feeders/runners
  * startup/teardown scripts