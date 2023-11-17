from time import sleep

import redis

if __name__ == '__main__':
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    previous = None
    while True:
        latest = r.zrevrange('latest_commands', 0, 19)
        if latest != previous:
            with open("latest_commands.txt", "w") as scratch_file:
                for action in latest:
                    username = action.split('#')[0]
                    display = action.split('#')[1]

                    scratch_file.write(f'{username}: {display}\n')

            scratch_file.close()
            previous = latest

        sleep(1)
