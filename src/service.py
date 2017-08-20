'''
Android python service
'''

from kivy.lib import osc

import time
import threading
from tracker import SpendingTracker, load_credentails

MAX_LOG_LENGTH = 1000
log_buffer = []

def log(message):
    print(message)
    message = str(message)
    log_buffer.append(message)
    if len(log_buffer) > MAX_LOG_LENGTH:
        log_buffer.pop(0)
    osc.sendMsg('/log', [message], port=9001)


def on_getLog(message, *largs):
    print("LOG requested")
    osc.sendMsg('/log', ["GET_LOG_START"], port=9001)

    for message in log_buffer[:]:
        osc.sendMsg('/log', ["GET_LOG_HISTORY::@" + message], port=9001)
    osc.sendMsg('/log', ["GET_LOG_FINISHED"], port=9001)

def read_loop(oscid):
    while True:
        osc.readQueue(oscid)
        time.sleep(0.5)

if __name__ == '__main__':
    osc.init()
    oscid = osc.listen(port=13920)
    osc.bind(oscid, on_getLog, '/getLog')

    threading.Thread(target=read_loop, args=(oscid,)).start()

    log("Android service started")

    credentials = load_credentails()

    if credentials:
        SpendingTracker.DEV = False

        try:

            tracker = SpendingTracker(credentials, log_function=log)

            if tracker.get_api().is_logged_in():
                log("Main loop started")
                while tracker.poll():
                    tracker.random_sleep()

                log("Tracking stopped")
        except Exception as e:
            log(str(e))
    else:
        log("Credentials error")