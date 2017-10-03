import threading
import traceback
from kivy.core.window import Window

from kivy.lib import osc

import sys

import time
from kivy.properties import StringProperty, Clock
from kivy.app import App
from kivy.utils import platform
from kivy.uix.scrollview import ScrollView

from tracker import SpendingTracker, load_credentails

from kivy.lang import Builder

Builder.load_string('''
<LogView>:
    Label:
        size_hint_y: None
        height: self.texture_size[1]
        text_size: self.width, None
        text: root.text
''')

class LogView(ScrollView):
    text = StringProperty('')


class TrackerApp(App):
    DEV = False
    stop_event = threading.Event()

    def log(self, message):
        print(message)
        self.log_to_screen(message)

    def receive_log_message(self, message, *args):
        if message[2] == "GET_LOG_START":
            self.log_buffer = []
            self.log_queue_buffer = []
            self.receiving_log_history = True

        elif message[2] == "GET_LOG_FINISHED":
            self.receiving_log_history = False
            for queued_message in self.log_queue_buffer:
                self.receive_log_message(queued_message)

        elif self.receiving_log_history:
            if "GET_LOG_HISTORY::@" in message[2]:
                self.log_to_screen(message[2].replace("GET_LOG_HISTORY::@", ""))
            else:
                self.log_queue_buffer.append(message)
        else:
            if "LOG_REPLACE_PREVIOUS::@" in message[2]:
                # Replace previous message and don't scroll
                self.log_replace_previous(message[2].replace("LOG_REPLACE_PREVIOUS::@", ""))
            else:
                self.log_to_screen(message[2])

    def log_replace_previous(self, message):
        self.log_buffer.pop()
        self.log_buffer.append(message)
        self.scrollable_text.text = "\n".join(self.log_buffer)

    def log_to_screen(self, message):
        if len(message.split("\n")) > 1:
            for line in message.split("\n"):
                self.log_buffer.append(line)
        else:
            self.log_buffer.append(message)

        while len(self.log_buffer) > 50:
            self.log_buffer.pop(0)


        self.scrollable_text.text = "\n".join(self.log_buffer)
        self.scrollable_text.scroll_y = 0

    def start_tracker_service(self):
        self.log("Starting android service")
        from jnius import autoclass

        trackerService = autoclass('com.freshollie.cashpassporttracker.ServiceTransactiontrackerservice')
        mActivity = autoclass('org.kivy.android.PythonActivity').mActivity

        argument = ''
        trackerService.start(mActivity, argument)

    def on_stop(self):
        if self.clock:
            self.clock.cancel()
        else:
            self.stop_event.set()
        Window.close()
        sys.exit()
        return True

    def on_start(self):
        self.log("App started")

        if platform == 'android':
            # If we are on android we run the tracker as a service so
            # It is not closed in the background

            self.log("Starting tracker service")

            osc.init()
            oscid = osc.listen(port=9001)

            # Listen to updates from service
            osc.bind(oscid, self.receive_log_message, '/log')

            # Send an update asking if the currently running service has a log we can display
            osc.sendMsg('/getLog', port=13920)

            # Read incoming messages
            self.clock = Clock.schedule_interval(lambda *x: osc.readQueue(oscid), 0)

            self.start_tracker_service()

        else:
            # Start the service inside the app if we are just running on a normal OS
            self.tracking_thread = threading.Thread(target=self.start_tracker)
            self.tracking_thread.start()

    def start_tracker(self):
        credentials = load_credentails()
        SpendingTracker.DEV = TrackerApp.DEV

        # Used to track if the service has crashed twice in a row
        crashed_before = False

        while True:
            try:
                tracker = SpendingTracker(credentials, log_function=self.log)

                if tracker.get_api().is_logged_in():
                    self.log("Main loop started")
                    while not self.stop_event.is_set() and tracker.poll():
                        crashed_before = False
                        sleep_time = tracker.get_random_sleep_time()
                        self.log("Refreshing in: " + str(sleep_time) + " seconds")

                        for i in range(sleep_time):
                            self.log_replace_previous("Refreshing in: " + str(sleep_time - (i + 1)) + " seconds")
                            time.sleep(1)
                            if self.stop_event.is_set():
                                break

                    self.log("Tracking stopped")
                    if self.stop_event.is_set():
                        return

                    self.log("Tracker service error")

            except Exception as e:
                self.log(traceback.format_exc())

            if not crashed_before:
                crashed_before = True
                self.log("Spending tracker crashed, attempting restart")
            else:
                break
        self.stop()

    def build(self):
        self.clock = None
        self.log_buffer = []
        self.log_queue_buffer = []
        self.receiving_log_history = False
        self.scrollable_text = LogView(text="")
        return self.scrollable_text

if __name__ == '__main__':
    TrackerApp().run()