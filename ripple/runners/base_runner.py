import os
import re
import json
import requests
from ripple import logger, RippleConfig


class BaseRunner():
    """
    A base class for job runners. This will define
    the interface for interacting with various runners.
    """

    def submit_job(self, job):
        """
        Dispatch a job for execution
        """
        pass

    def get_job_status(self, job):
        """
        Check the status for a job
        """
        pass

    def report_job(self, job):
        """
        Report the job has been run.
        """
        logger.debug("Reporting job.")
        payload = {'endpoint_uuid': RippleConfig().endpoint_id,
                   'status_code': 'COMPLETE', 'status_message': 'run',
                   'event': job, 'job_id': job['job_id'],
                   'output': job['output'], 'err': job['err']}
        logger.debug(payload)
        r = requests.post(RippleConfig().update_status_path, json=payload)
        data = json.loads(r.text)
        return data

    def set_targets(self, job):
        if job['parameters']['target_match'] is not None:
            # work out what the target should be (could be
            # regex of the trigger file -- e.g. diff extension)
            # e.g. change extension to .h5: filename =
            # re.sub('\.(.*)', '.h5', event['event']['pathname'])
            job['target_pathname'] = re.sub(
                                        job['parameters']['target_match'],
                                        job['parameters']['target_replace'],
                                        job['pathname'])
        elif job['parameters']['target_replace'] is not None:
            # just replace the whole string
            job['target_pathname'] = job['parameters']['target_replace']
        else:
            # otherwise, set the target to be the filename
            job['target_pathname'] = job['pathname']

        # now work out the filename and path
        event_path = job['target_pathname'].rsplit(os.sep, 1)[0]
        file_name = job['target_pathname'].rsplit(os.sep, 1)[1]
        job['target_path'] = event_path
        job['target_name'] = file_name
        if file_name is None or file_name == '':
            job['target_name'] = job['target_pathname']
        print (job)
        return job
