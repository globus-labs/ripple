from string import Template
import subprocess
from ripple.runners.base_runner import BaseRunner
from ripple import logger
import os
import fcntl
import time

class ShellRunner(BaseRunner):
    """
    A job runner for shell commands.
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
        Start a subprocess to execute the command
        """
        job = self.set_targets(job)
        logger.info("In shell submit command")
        cmd = job['parameters']['cmd']
        job['output'] = ''
        job['err'] = ''
        if '$' in cmd:
            args = {'filename': job['target_name'].replace("/~/", ""),
                    'path': job['target_path'],
                    'pathname': job['target_pathname']}
            cmd = Template(cmd).substitute(args)
        logger.info("Executing '%s'" % cmd)

        p = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        # Give it a few seconds then report the output
        time.sleep(3)
        job['output'] = self.non_block_read(p.stdout)
        job['err'] = self.non_block_read(p.stderr)

        return p.pid
