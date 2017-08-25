'''
Android python service
'''
import random
from kivy.lib import osc

import sys
import traceback

import time
import threading
from tracker import SpendingTracker, load_credentails

MAX_LOG_LENGTH = 1000
log_buffer = []

RUNNING = False


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
    while RUNNING:
        osc.readQueue(oscid)
        time.sleep(0.5)
    osc.dontListen()


def random_wait_notify_progress():
    random_amount = random.randint(60 * 60 * 3, 60 * 60 * 5)
    log("Waiting for " + str(random_amount) + " seconds")
    log(str(1))
    for i in range(1, random_amount):
        log_buffer.pop()
        log_buffer.append(str(i))
        osc.sendMsg('/log', ["LOG_REPLACE_PREVIOUS::@" + str(i)], port=9001)
        time.sleep(1)

if __name__ == '__main__':
    RUNNING = True
    osc.init()
    oscid = osc.listen(port=13920)
    osc.bind(oscid, on_getLog, '/getLog')

    threading.Thread(target=read_loop, args=(oscid,)).start()

    log("Android service started")

    credentials = load_credentails()

    if credentials:
        # True means it won't connect the web
        SpendingTracker.DEV = False

        # Used to track if the service has crashed twice in a row
        crashed_before = False

        while True:
            try:
                tracker = SpendingTracker(credentials, log_function=log)

                if tracker.get_api().is_logged_in():
                    log("Main loop started")
                    while tracker.poll():
                        crashed_before = False
                        random_wait_notify_progress()

                    log("Tracker service error")

            except Exception as e:
                log(traceback.format_exc())

            if not crashed_before:
                crashed_before = True
                log("Spending tracker crashed, attempting restart")
            else:
                break
    else:
        log("Credentials error")

    log("Service crashed. Restart app")
    RUNNING = False
    sys.exit(1)