import subprocess
from ripple.runners.base_runner import BaseRunner
from ripple import logger


class SlurmRunner(BaseRunner):
    """
    A job runner for slurm jobs.
    """

    def submit_job(self, job):
        """
        I wanted to use pyslurm for this, but I believe it is designed
        for admins, rather than end users. I didn't see a nice way to
        dispatch jobs. Instead, this will just start a subprocess to
        start the job, but then use pyslurm to check the jobs status etc.
        Start a subprocess to execute the command
        """
        job = self.set_targets(job)
        logger.info("In slurm submit command")
        cmd = "cd %s; sbatch %s" % (job['target_path'], job['target_file'])
        logger.info("Executing '%s'" % cmd)
        subprocess.Popen([cmd], shell=True)
