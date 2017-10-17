import os
import time
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver

from ripple.observers.base_observer import BaseObserver
from ripple import logger, RippleConfig


class PosixObserver(BaseObserver):
    """
    Use the Watchdog module to observe filesystem events.
    """
    def monitor(self):
        # Set up the event handler
        event_handler = MyEventHandler(
                           patterns=['*'],
                           ignore_patterns=['version.py'],
                           ignore_directories=True)
        event_handler.setup(self)
        # Extract the set of directories to listen to
        listen_dirs = self.get_dirs_to_monitor()

        # Create an observer and schedule each of the directories
        self.observer = Observer()
        logger.debug("Starting observer: %s" % RippleConfig().monitor)
        if RippleConfig().monitor == "poll":
            self.observer = PollingObserver()

        for d in listen_dirs:
            # Put this in a try so it doesn't crash if the dir doesnt exist
            if os.path.isdir(d):
                logger.info("Monitoring: %s" % d)
                self.observer.schedule(event_handler, d, recursive=True)
            else:
                logger.error("Directory does not exist: %s" % d)
        try:
            self.observer.start()
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_monitoring()
        self.observer.join()

    def get_dirs_to_monitor(self):
        """
        Work out which directories to monitor.
        """
        rules = RippleConfig().rules
        listen_dirs = []
        for rule in rules:
            if rule['trigger']['monitor'] == 'filesystem':
                listen_dirs.append(rule['trigger']['parameters']['directory'])
        listen_dirs = list(set(listen_dirs))
        logger.debug("Monitoring dirs: %s" % listen_dirs)

        return listen_dirs

    def stop_monitoring(self):
        """
        Terminate the monitor
        """
        logger.debug("Terminating POSIX monitor.")
        self.observer.stop()


class MyEventHandler(PatternMatchingEventHandler):

    def setup(self, monitor):
        self.monitor = monitor

    def on_any_event(self, event):
        """
        This is executed if any event is detected. Could be useful for
        doing some admin work later.
        """
        #logger.info("Captured POSIX event: %s" % event)
        # Check if any rule should be applied for this event
        self.monitor.check_rules(event)
