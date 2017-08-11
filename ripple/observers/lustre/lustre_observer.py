import sys, os
import time
import threading
import subprocess
import uuid
import re
import hashlib
import json

from ripple.observers.base_observer import BaseObserver
from ripple import logger, RippleConfig

class LustreObserver(BaseObserver):
    def monitor(self):
        self.lustre_path = "/mnt/scratch/"
        self.events = []
        # get the tasks
        self.last_eid = '0'
        t3 = threading.Thread(target=self.observe_changelogs)
        t3.daemon = True
        t3.start()

    def observe_changelogs(self):
        while True:
            # sudo lfs changelog scratch-MDT0000
            events = subprocess.check_output(["lfs", "changelog", "scratch-MDT0000"])
            print(events)
            # do the reverse look up on each event
            event_list = []
            for event in events.split('\n'):
                event_data = event.split(" ")
                if len(event_data) < 2:
                    continue
                fid = ''
                # for e in event_data:
                #     if 't=[' in e:
                #         fid = e[e.find("[")+1:e.find("]")]
                #         if fid not in self.events:
                #         # lfs fid2path /mnt/scratch 0x200000401:0x5:0x0
                #             src_path = subprocess.check_output(["lfs", "fid2path", self.lustre_path, fid])
                self.on_any_event(event)
                            # event_list.append({'fid': fid, 'src_path' : src_path, 'type' : event_data[1], 'id' : event_data[0]})

            print(event_list)
            time.sleep(1)
            print("looping")
            # sys.exit(0)

    def on_any_event(self, event):
    	"""
		Raise an event to be processed.
    	"""
    	self.check_rules(event)
    	subprocess.check_output(["lfs", "changelog_clear", "scratch-MDT0000", "cl1", self.last])

    def check_rules(self, event):
        """
        Try to match a rule to this event. If nothing is found, return None
        """
        logger.debug("Checking rules")
        event_data = event.split(" ")
        fid = ''
        eid = event_data[0]
        self.last = eid
        event_type = event_data[1]
        src_path = ''
        for e in event_data:
            if 't=[' in e:
                fid = e[e.find("[")+1:e.find("]")]
                if fid not in self.events:
                # lfs fid2path /mnt/scratch 0x200000401:0x5:0x0
                    src_path = subprocess.check_output(["lfs", "fid2path", self.lustre_path, fid])
        # Extract the file and path names
        # src_path = os.path.abspath(event.src_path)
        event_path = src_path.rsplit(os.sep, 1)[0]
        file_name = src_path.rsplit(os.sep, 1)[1]


        # Iterate through rules and try to apply them
        for rule in RippleConfig().rules[:]:
            if self.match_condition(event_type, event_path, file_name, rule):
                send_event = {'event' : {
                             'type' : event_type,
                             'pathname' : src_path,
                             'path' : event_path,
                             'name' : file_name,
                             'uuid' : str(uuid.uuid4()) ,
                             'hash' : 'hashvalue'
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

                # self.add_event_to_db(send_event)

                # Check if it is a new set of rules to load
                # if rule['action']['type'] == 'rules':
                #     if rule['action']['process']:
                #         self.load_rules(src_path)
        return None
