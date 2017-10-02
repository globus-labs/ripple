import time
import json
import requests
from ripple.runners.shell.shell_runner import ShellRunner
from ripple.runners.slurm.slurm_runner import SlurmRunner

from ripple import logger, RippleConfig


class RippleRunner():

    def __init__(self):
        RippleConfig()
        self.completed_jobs = []

    def run(self):
        """
        Execute jobs.
        """
        # Because this doesn't have an API for the cloud
        # to submit jobs, start by polling for new ones.
        self.executions = []
        while True:
            self.jobs = self.poll_for_jobs()

            for job in self.jobs:
                try:
                    job = json.loads(job)
                    if job['event_uuid'] not in self.completed_jobs:
                        result = self.execute_job(job)

                        self.record_finished_job(job, result)
                except Exception as e:
                    logger.error("Failed to execute job.")
                    logger.error(job)
                    logger.error(e)

            time.sleep(float(RippleConfig().runner_poll_rate))

    def record_finished_job(self, job, result):
        """
        Keep a local log of finished job ids so it won't try
        to repeat
        """
        self.completed_jobs.append(job['event_uuid'])
        return

    def execute_job(self, job):
        """
        Work out which job runner to use then pass it to it
        """

        # TODO: It seems like this would be better if the base
        # class decided which runner to make based on the job.
        if job['service'] == 'filesystem':
            if job['action_type'] == 'subprocess':
                runner = ShellRunner()
                runner.submit_job(job)
                runner.report_job(job)
            if job['action_type'] == 'singularity':
                pass
        if job['service'] == 'batch':
            if job['action_type'] == 'slurm':
                runner = SlurmRunner()
                runner.submit_job(job)
                runner.report_job(job)

    def poll_for_jobs(self):
        """
        Without an API to accept jobs, reach out to the cloud
        API and request jobs for this endpoint.
        """
        payload = {'Endpoint': RippleConfig().endpoint_id}
        data = {}
        try:
            r = requests.post(RippleConfig().get_jobs_path, data=payload)
            data = json.loads(r.text)
            
        except Exception as e:
            logger.error("Did not receive proper json when polling for jobs.")
            logger.error(e)
        # logger.debug("Runner: polled new job: %s" % data)
        return data
