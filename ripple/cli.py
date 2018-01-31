import logging
import threading
import time
import os
from ripple import (logger, RippleAgent, RippleProcessor,
                    RippleRunner, RippleConfig)


def get_rules():
    """
    Load the rules for this agent.
    """
    # threading.Timer(10.0, get_rules).start()
    while True:
        RippleConfig().load_rules()
        time.sleep(30)


def main():
    """
    Configure a logger (ripple.log).

    Start four threads to run the ripple agent:
        1. a thread to periodically retrieve rules from the API
        2. a thread for the local monitoring agent
        3. a proccessing thread that will report events to the API
        4. a thread for the job runner
    """
    hdlr = logging.FileHandler(os.path.expanduser('~') +'/.ripple/ripple.log')

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.DEBUG)
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(formatter)
    logger.addHandler(consoleHandler)

    # Start the four threads and set to daemon so they exit on ctrl-c
    ripple = RippleAgent()
    t0 = threading.Thread(target=get_rules)
    t0.daemon = True

    ripple = RippleAgent()
    t1 = threading.Thread(target=ripple.run)
    t1.daemon = True

    processor = RippleProcessor()
    t2 = threading.Thread(target=processor.run)
    t2.daemon = True

    runner = RippleRunner()
    t3 = threading.Thread(target=runner.run)
    t3.daemon = True

    t0.start()
    t1.start()
    t2.start()
    t3.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
