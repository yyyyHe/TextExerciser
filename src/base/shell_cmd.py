# -*- coding: utf-8 -*-
import subprocess
import sys
import shlex
import psutil


def execute_simply(cmd):
    subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)


def execute(cmd, stdout=sys.stdout, quiet=False, shell=False, raise_exceptions=True, use_shlex=True, timeout=None):
    """
    Exec command by command line like 'ln -ls "/var/log"'
    """
    if not quiet:
        print("Run %s", str(cmd))
    if use_shlex and isinstance(cmd, (str, str)):
        cmd = shlex.split(cmd)
    if timeout is None:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)
        out, err = process.communicate()
    else:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)
        p = psutil.Process(process.pid)
        out, err = process.communicate()
        finish, alive = psutil.wait_procs([p], timeout)
        if len(alive) > 0:
            ps = p.children()
            ps.insert(0, p)
            print('waiting for timeout again due to child process check')
            finish, alive = psutil.wait_procs(ps, 0)
        if len(alive) > 0 or len(err) > 0:
            print('process {} will be killed'.format([p.pid for p in alive]))
            for p in alive:
                p.kill()
            if raise_exceptions:
                print('External program timeout at {} {}'.format(timeout, cmd))
                raise TimeoutError('Timeout : ' + str(cmd))
    retcode = process.returncode
    if retcode and raise_exceptions:
        print("External program failed %s", str(cmd))
        raise ValueError('Faile : ' + str(cmd))
    return [line.replace('\r', '') for line in out.decode('utf-8').split('\n') if len(line) > 0], \
           [line.replace('\r', '') for line in err.decode('utf-8').split('\n') if len(line) > 0]
