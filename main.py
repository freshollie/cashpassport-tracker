import threading

import time
from kivy.properties import StringProperty

from kivy.adapters.simplelistadapter import SimpleListAdapter

import kivy
from kivy.app import App
from kivy.clock import mainthread
from kivy.uix.label import Label
from kivy.uix.listview import ListView
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

import sys

from tracker import SpendingTracker

from kivy.lang import Builder

Builder.load_string('''
<ScrollableLabel>:
    Label:
        size_hint_y: None
        height: self.texture_size[1]
        text_size: self.width, None
        text: root.text
''')

class ScrollableLabel(ScrollView):
    text = StringProperty('')

class MyApp(App):
    stop_event = threading.Event()

    def on_stop(self):
        # The Kivy event loop is about to stop, set a stop signal;
        # otherwise the app window will close, but the Python process will
        # keep running until all secondary threads exit.
        self.stop_event.set()

    def log(self, message):
        print(message)

        if len(message.split("\n")) > 1:
            for line in message.split("\n"):
                self.log_buffer.append(line)
        else:
            self.log_buffer.append(message)

        self.scrollable_text.text = "\n".join(self.log_buffer)
        self.scrollable_text.scroll_y = 0

    def start_tracker(self):
        credentials = []
        with open("credentials.conf", "r") as creds_file:
            for credential in creds_file.readlines():
                credentials.append(credential.strip())
        SpendingTracker.DEV = True

        tracker = SpendingTracker(credentials, log_function=self.log)

        if tracker.get_api().is_logged_in():
            self.log("Main loop started")
            while not self.stop_event.is_set() and tracker.poll():
                tracker.random_sleep()
            self.log("Tracking stopped")

    def build(self):
        #simple_list_adapter = SimpleListAdapter(data=[], cls=MyLabel)

        #self.lv = ListView(adapter=simple_list_adapter)
        self.log_buffer = []
        self.scrollable_text = ScrollableLabel(text="")
        self.tracking_thread = threading.Thread(target=self.start_tracker)
        self.tracking_thread.start()
        return self.scrollable_text

if __name__ == '__main__':
    MyApp().run()