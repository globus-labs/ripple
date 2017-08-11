import time
import threading
from ripple.observers.posix.posix_observer import PosixObserver
from ripple.observers.lustre.lustre_observer import LustreObserver
from ripple import logger, RippleConfig


class RippleAgent():

    def __init__(self):
        RippleConfig()

    def run(self):
        """
        Start observers for the given rules.
        """
        logger.debug("Starting agent.")
        mon_thread = None
        try:
            while True:
                if RippleConfig().new_rules:
                    # I need to use a stoppable thread or make the thread set
                    # the observer to stop
                    if mon_thread is not None:
                        mon_thread = None
                    # the watchdog monitor is blocking, so we need
                    # to start it as a thread in order to restart it
                    # when new rules are detected
                    mon_thread = threading.Thread(target=self.set_observers)
                    mon_thread.daemon = True
                    mon_thread.start()
                    RippleConfig().new_rules = False
                time.sleep(5)

        except KeyboardInterrupt:
            try:
                self.watchdog_ob.stop()
                self.watchdog_ob.join()
            except:
                pass

    def set_observers(self):
        """
        Set the observers.
        """
        try:
            self.watchdog_ob.stop()
            self.watchdog_ob.join()
        except Exception:
            pass

        if RippleConfig().monitor == "inotify":
            self.watchdog_ob = PosixObserver()
            self.watchdog_ob.monitor()
        elif RippleConfig().monitor == "lustre":
            self.lustre_mon = LustreObserver()
            self.lustre_mon.monitor()
