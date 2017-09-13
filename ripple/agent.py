import time
import threading
from ripple.observers.posix.posix_observer import PosixObserver
from ripple.observers.lustre.lustre_observer import LustreObserver
from ripple.observers.ipc.ipc_observer import IPCObserver
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
                    # I need to use a stoppable thread or make
                    # the thread set the observer to stop
                    if mon_thread is not None:
                        mon_thread = None
                    # the watchdog monitor is blocking, so we need
                    # to start it as a thread in order to restart it
                    # when new rules are detected
                    mon_thread = threading.Thread(target=self.set_observers)
                    mon_thread.daemon = True
                    mon_thread.start()
                    RippleConfig().new_rules = False
                time.sleep(15)

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
        mon = RippleConfig().monitor
        if mon == "inotify" or mon == "poll":
            self.watchdog_ob = PosixObserver()
            self.watchdog_ob.monitor()
        elif mon == "lustre":
            self.lustre_mon = LustreObserver()
            self.lustre_mon.monitor()
        elif mon == "ipc":
            self.ipc_mon = IPCObserver()
            self.ipc_mon.monitor()
