import subprocess
from ripple.runners.base_runner import BaseRunner
from ripple import logger
import os
import time
import fcntl

class SlurmRunner(BaseRunner):
    """
    A job runner for slurm jobs.
    """

    def non_block_read(self, output):
        fd = output.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        try:
            return str(output.read())
        except:
            return ""

    def submit_job(self, job):
        """
        I wanted to use pyslurm for this, but I believe it is designed
        for admins, rather than end users. I didn't see a nice way to
        dispatch jobs. Instead, this will just start a subprocess to
        start the job, but then use pyslurm to check the jobs status etc.
        Start a subprocess to execute the command
        """
        job = self.set_targets(job)
        job['output'] = ''
        job['err'] = ''
        logger.info("In slurm submit command")
        cmd = "cd %s; sbatch %s" % (job['target_path'], job['target_name'])
        logger.info("Executing '%s'" % cmd)
        p = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        # Give it a few seconds then report the output
        time.sleep(3)
        job['output'] = self.non_block_read(p.stdout)
        job['err'] = self.non_block_read(p.stderr)
