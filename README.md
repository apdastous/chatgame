# HOWTO
* Set up rabbitmq
* Create settings.py and add the following:
  * AMQP_URL
  * TWITCH_NICKNAME
  * TWITCH_CHANNEL
  * TWITCH_OAUTH_TOKEN
  * TWITCH_AMQP_QUEUE
* Run twitch.py, you should see messages published for each line of twitch chat
* Run duckstation.py and check gamepad inputs


# Chat controls
**Button inputs**
* triangle
* cross
* square
* circle
* r1
* r2
* l1
* l2

**D-pad inputs**
* dup
* ddown
* dleft
* dright

**Left thumbstick inputs**
* tlup
* tldown
* tlleft
* tlright

**Modifiers**

To hold circle button for three seconds:
* circle:3

To press d-pad down five times quickly:
* ddown:5

To hold left thumbstick in down position for 6 seconds:
* tldown:6

# TODO
* Threaded rabbitmq client
  * send proper heartbeats
  * aiopika?
* Multi-button inputs
* Project structure
  * separate into feeders/runners
  * startup/teardown scripts
