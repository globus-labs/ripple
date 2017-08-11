import os
import json
import sys
import re
from string import Template
import requests
from ripple import logger, RippleConfig


class RippleProcessor():

    def __init__(self):
        self.failures = {}

    def run(self):
        self.poll_events()

    def report_event(self, event):
        """
        Send a POST request to the API's event reporting path
        """
        logger.error("Publishing event.")
        logger.info(RippleConfig().report_event_path)

        r = requests.post(RippleConfig().report_event_path, json=event)
        logger.info("Response: %s %s" % (r.status_code, r.reason))

        # Check it was successfully registered, otherwise try again
        # Note: this returns 500 at the moment as I haven't configured
        # a response integration with SNS.
        if r.status_code == requests.codes.ok or r.status_code == 500:
            logger.info("Successfully reported event.")
            return
        else:
            logger.error("Failed to register event. %s" % event)
            logger.error("Status code. %s" % r.status_code)
            fail_count = 1
            if event['event']['uuid'] in self.failures:
                fail_count = self.failures[event['event']['uuid']] + 1
            self.failures[event['event']['uuid']] = fail_count
            if fail_count < 3:
                # add it back on to the queue and try again
                message = json.dumps(event)
                RippleConfig().queue.put(message)

    def poll_events(self):
        """
        Check the queue for events to process
        """
        while True:
            body = RippleConfig().queue.get()
            event = json.loads(body)

            # Clean up the event by setting the target and replacing strings
            event = self.set_target(event)
            event = self.template_parameters(event)

            logger.info("PROCESSOR: received event: %s" % event)
            self.report_event(event)

    def template_parameters(self, event):
        params = event['action']['parameters']
        args = {'filename': event['action']['target_name'].replace("/~/", ""),
                'path': event['action']['target_path'],
                'pathname': event['action']['target_pathname']}

        for k, val in params.items():
            if '$' in val:
                params[k] = Template(val).substitute(args)

        event['action']['parameters'] = params
        return event

    def set_target(self, event):
        """
        This is designed to let you specify a rule that will act on a
        file other than the trigger. This function should return the
        event with an updated target_path, target_pathname, target_name
        based on the event['action']['target'] regex
        """
        new_path = event['action']['target_pathname']
        if event['action']['target_match'] is not None:
            # work out what the target should be (could be regex of
            # the trigger file -- e.g. diff extension)
            # e.g. change extension to .h5: filename = re.sub('\.(.*)',
            # '.h5', event['event']['pathname'])
            new_path = re.sub(event['action']['target_match'],
                              event['action']['target_replace'],
                              event['event']['pathname'])
        elif event['action']['target_replace'] is not None:
            # just replace the whole string
            new_path = event['action']['target_replace']
        else:
            # otherwise, set the target to be the filename
            new_path = event['event']['pathname']
        event['action']['target_pathname'] = new_path
        # now work out the filename and path
        event_path = event['action']['target_pathname'].rsplit(os.sep, 1)[0]
        file_name = event['action']['target_pathname'].rsplit(os.sep, 1)[1]
        event['action']['target_path'] = event_path
        event['action']['target_name'] = file_name
        if file_name is None or file_name == '':
            event['action']['target_name'] = event['action']['target_pathname']
        return event
