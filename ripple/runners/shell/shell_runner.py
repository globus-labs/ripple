from string import Template
import subprocess
from ripple.runners.base_runner import BaseRunner
from ripple import logger


class ShellRunner(BaseRunner):
    """
    A job runner for shell commands.
    """

    def submit_job(self, job):
        """
        Start a subprocess to execute the command
        """
        job = self.set_targets(job)
        logger.info("In shell submit command")
        cmd = job['parameters']['cmd']
        if '$' in cmd:
            args = {'filename': job['target_name'].replace("/~/", ""),
                    'path': job['target_path'],
                    'pathname': job['target_pathname']}
            cmd = Template(cmd).substitute(args)
        logger.info("Executing '%s'" % cmd)

        p = subprocess.Popen([cmd], shell=True)
        return p.pid
