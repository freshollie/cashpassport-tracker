import threading
from kivy.core.window import Window

from kivy.lib import osc
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

LOGPORT = 13892

class LogView(ScrollView):
    text = StringProperty('')


class TrackerApp(App):
    stop_event = threading.Event()

    def log(self, message):
        print(message)
        self.log_to_screen(message)

    def receive_log_message(self, message, *args):
        if message[2] == "GET_LOG_START":
            self.log_buffer = []
            self.log_queue_buffer = []
            self.receiving_log_history = True
            return

        if message[2] == "GET_LOG_FINISHED":
            self.receiving_log_history = False
            for queued_message in self.log_queue_buffer:
                self.log_to_screen(queued_message)
            return

        if self.receiving_log_history:
            if "GET_LOG_HISTORY::@" in message[2]:
                self.log_to_screen(message[2].replace("GET_LOG_HISTORY::@", ""))
            else:
                self.log_queue_buffer.append(message[2])
        else:
            self.log_to_screen(message[2])

    def log_to_screen(self, message):
        if len(message.split("\n")) > 1:
            for line in message.split("\n"):
                self.log_buffer.append(line)
        else:
            self.log_buffer.append(message)

        if len(self.log_buffer) > 100:
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
        return True

    def on_pause(self):
        self.stop()

    def on_start(self):
        self.log("App started")

        if platform == 'android':
            self.service_alive = False

            self.log("Starting tracker service")

            osc.init()
            oscid = osc.listen(port=9001)
            osc.bind(oscid, self.receive_log_message, '/log')
            osc.sendMsg('/getLog', port=13920)
            self.clock = Clock.schedule_interval(lambda *x: osc.readQueue(oscid), 0)

            self.start_tracker_service()

        else:
            self.tracking_thread = threading.Thread(target=self.start_tracker)
            self.tracking_thread.start()

    def start_tracker(self):
        credentials = load_credentails()
        SpendingTracker.DEV = False

        tracker = SpendingTracker(credentials, log_function=self.log)

        if tracker.get_api().is_logged_in():
            self.log("Main loop started")
            while not self.stop_event.is_set() and tracker.poll():
                tracker.random_sleep()
            self.log("Tracking stopped")
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