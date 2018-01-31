import os
import json
import re
import uuid
from ripple import logger, RippleConfig


class BaseObserver():

    def monitor(self):
        pass

    def check_rules(self, event):
        """
        Try to match a rule to this event. If nothing is found, return None
        """
        #logger.debug("Checking rules")

        # Extract the file and path names
        src_path = os.path.abspath(event.src_path)
        event_path = src_path.rsplit(os.sep, 1)[0]
        file_name = src_path.rsplit(os.sep, 1)[1]

        # if 'glink' in file_name:
        #     return

        # Iterate through rules and try to apply them
        for rule in RippleConfig().rules[:]:
            # We are potentially monitoring multiple paths, so check if the
            # rule should be applied to a file in this path (or subpath).
            event_type = type(event).__name__
            if self.match_condition(event_type, event_path, file_name, rule):
                # The filename matches the trigger regex -- now build
                # an event to send to lambda
                # TODO: add a has of these values so i know it is unique
                # m = hashlib.md5()

                send_event = {'event': {
                             'type': type(event).__name__,
                             'pathname': src_path,
                             'path': event_path,
                             'name': file_name,
                             'uuid': str(uuid.uuid4()),
                             'hash': 'hashvalue'
                             }
                            }
                send_event.update(rule)
                # check if it is a gcmd, if so, replace the action
                if re.match(file_name, '.*.gcmd'):
                    action = self.get_cmd(src_path)
                    if action:
                        send_event.update(action)

                # Set a target for this rule
                # send_event = self.set_target(send_event)

                # Now push it down the queue
                message = json.dumps(send_event)
                RippleConfig().queue.put(message)
                logger.debug("Sent data to queue")

        return None

    def match_condition(self, event_type, event_path, file_name, rule):
        """
        Match the event against a rule's conditions.
        """

        rule_dir = rule['trigger']['parameters']['directory']
        rule_event_type = rule['trigger']['event']
        rule_file_name = rule['trigger']['parameters']['match']
        #logger.debug("Matching rule conditions")
        #print("Matching rule conditions")
        # Use 'in' here to allow many trigger events on one rule.
        try:
            re.compile(rule_file_name)
        except re.error:
            logger.error("Invalid regex: %s" % rule_file_name)
            return False
        if event_type in rule_event_type:
            #logger.debug("Matching rule conditions: type MATCHED")
            # Fix the problem of Win32 machine's paths being
            if rule_dir[-1] == "/" and event_path[-1] != "/":
                # remove the last slash
                rule_dir = rule_dir[:-1]

            if re.match(rule_dir.replace('\\', '/'),
                        event_path.replace('\\', '/')):
                #logger.debug("Matching rule conditions: dir MATCHED")
                # Check the file name actually matches ours
                if re.match(rule_file_name, file_name):
                    #logger.debug("Matching rule conditions: file MATCHED")
                    return True
        return False

    def get_cmd(self, fileloc):
        """
        Try to load the file and get the action command from it.
        """
        try:
            with open(fileloc) as data_file:
                try:
                    data = json.load(data_file)
                    # print data
                    return data
                except Exception as e:
                    logger.error('Failed to read gcmd json.')
                    logger.error(e)
        except Exception as e:
            # file doesn't exist
            logger.debug("Failed to find .gcmd file %s" % fileloc)
        return None
