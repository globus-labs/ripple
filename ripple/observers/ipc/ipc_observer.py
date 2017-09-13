import os
import time
import subprocess
import sys
import uuid
import json
import re

from ripple.observers.base_observer import BaseObserver
from ripple import logger, RippleConfig


class IPCObserver(BaseObserver):
    """
    Set up the polling IPC monitor. It will use the
    "ipcs" command to query for shared memory segments
    and will report those that have been created and removed.
    """
    def monitor(self):
        self.segments = {}
        self.poll(True)

        while True:
            time.sleep(5)
            self.poll(False)

    def poll(self, start=False):
        """
        Use the ipcs command to get memory events and compare
        them against active rules. 
        """

        segments = self.get_segments(start)
        
        events = self.process_segments(segments)
        print (events)

        # now process the events against rules
        for event in events:
            self.check_rules(event)


    def check_rules(self, event):
        """
        Try to match a rule to this event. If nothing is found, return None
        They look like this:
        key        shmid      owner      perms      bytes      nattch     status      
        0x00000000 262145     ryan       600        393216     2          dest  
        """
        logger.debug("Checking rules")
        # Iterate through rules and try to apply them
        for rule in RippleConfig().rules[:]:
            event_type = event['type']
            if self.match_condition(event_type, rule):
                # Currently putting in pathname as key, need to
                # think of a better way to handle "other" information
                send_event = {'event': {
                             'type': event_type,
                             'size': event['bytes'],
                             'key': event['key'],
                             'pathname': event['key'],
                             'path': event['key'],
                             'filename': event['key'],
                             'shmid': event['shmid'],
                             'perms': event['perms'],
                             'owner': event['owner'],
                             'status': event['status'],
                             'uuid': str(uuid.uuid4()),
                             'hash': 'hashvalue'
                             }
                            }
                send_event.update(rule)

                # Now push it down the queue
                message = json.dumps(send_event)
                RippleConfig().queue.put(message)
                logger.debug("Sent data to queue")

        return None

    def match_condition(self, event_type, rule):
        """
        Match the event against a rule's conditions.
        """
        logger.debug("Matching rule conditions")
        rule_event_type = rule['trigger']['event']
        
        if event_type == rule_event_type:
            logger.debug("Matching rule conditions: type MATCHED")
            # Hm, might be worth adding perms, owner, status?
            return True
        return False


    def process_segments(self, segments):
        """
        Process the segments and return which are new and which have been removed.
        """
        previous = dict(self.segments)
        new = []
        removed = []
        for shmid, val in segments.items():
            if shmid not in previous.keys():
                new.append(val)
                # update it in the global dict
                self.segments[shmid] = val
            else:
                # it already existed, so ignore it
                del previous[shmid]

        for shmid, val in previous.items():
            removed.append(val)
            del self.segments[shmid]

        # now convert these into events
        events = []
        for e in new:
            e['type'] = 'Create'
            if 'status' not in e:
                e['status'] = 'other'
            events.append(e)
        for e in removed:
            if 'status' not in e:
                e['status'] = 'other'
            e['type'] = 'Delete'
            events.append(e)

        return events

    def get_segments(self, start=False):
        """
        Use the icps command to get and return a dictionary of
        segments.
        """
        cmd = ["ipcs", "-a"]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        output, err = process.communicate()
        output = output.decode("utf-8").split("\n")

        keys = ['key', 'shmid', 'owner', 'perms', 'bytes', 'nattch',
                'status']
        segments = {}

        for line in output:
            # this should capture all keys
            # note: it won't do queues vs mem vs sem etc.
            if line[0:2] == '0x':
                values = list(filter(None, line.split(" ")))
                data = dict(zip(keys, values))
                if start:
                    # print (data['shmid'])
                    self.segments[data['shmid']] = data
                segments[data['shmid']] = data
        return segments

    def stop_monitoring(self):
        """
        Terminate the monitor
        """
        logger.debug("Terminating POSIX monitor.")
