"""Explicitly authorized local checks with argument arrays and minimal environments.

This runner is not a sandbox. Authorized target code retains the caller's OS
permissions and can open local files or networks. No output or secret values are
included in reports. Timeouts terminate the local process group where supported.
"""

import math
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

from .common import ToolkitError, digest, json_bytes

DENIED = {'sh', 'bash', 'zsh', 'fish', 'cmd', 'powershell', 'pwsh', 'git',
          'curl', 'wget', 'ssh', 'scp', 'pip', 'npm', 'npx', 'rm', 'rmdir', 'del',
          'erase', 'format', 'diskpart', 'shutdown', 'sudo', 'doas', 'env'}


def run_check(check, root, allow_exec=False, pass_env=()):
    if (not isinstance(check, dict) or set(check) - {'name', 'argv', 'timeout', 'retries'}
            or not isinstance(check.get('name'), str) or not check['name']
            or not isinstance(check.get('argv'), list) or not check['argv']
            or any(not isinstance(a, str) or '\x00' in a for a in check['argv'])):
        raise ToolkitError('check needs name and an argument array; shell strings are unsupported')
    timeout, retries = check.get('timeout', 60), check.get('retries', 0)
    if (type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 300
            or type(retries) is not int or not 0 <= retries <= 2):
        raise ToolkitError('timeout must be finite in (0, 300]; retries must be in [0, 2]')
    argv = list(check['argv'])
    if argv[0] == 'python':
        argv[0] = sys.executable
    if Path(argv[0]).stem.casefold() in DENIED:
        raise ToolkitError('shell, remote, package-manager and git executables are not supported by the local check runner')
    label = digest(check['name'].encode('utf-8'))[:12]
    result = {'check_id': label, 'argv_sha256': digest(json_bytes(argv)), 'attempts': [],
              'status': 'UNKNOWN', 'classification': 'execution_not_authorized'}
    if not allow_exec:
        return result
    env = {name: os.environ[name] for name in ('PATH', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP') if name in os.environ}
    env.update({'PYTHONNOUSERSITE': '1', 'PYTHONDONTWRITEBYTECODE': '1'})
    for name in pass_env:
        if not re.fullmatch('[A-Za-z_][A-Za-z0-9_]*', name):
            raise ToolkitError('invalid explicitly forwarded environment name')
        if name in os.environ:
            env[name] = os.environ[name]
    for _ in range(retries + 1):
        started = time.perf_counter()
        try:
            proc = subprocess.Popen(argv, cwd=str(root), env=env, stdin=subprocess.DEVNULL,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                    shell=False, start_new_session=os.name != 'nt')
        except OSError:
            result.update(status='FAIL', classification='cannot_start')
            result['attempts'].append({'returncode': None, 'seconds': time.perf_counter() - started})
            break
        try:
            rc = proc.wait(timeout=timeout)
            result.update(status='PASS' if rc == 0 else 'FAIL',
                          classification='success' if rc == 0 else 'nonzero_exit')
        except subprocess.TimeoutExpired:
            if os.name == 'nt':
                system = Path(os.environ.get('SYSTEMROOT', 'C:/Windows')) / 'System32/taskkill.exe'
                try:
                    subprocess.run([str(system), '/PID', str(proc.pid), '/T', '/F'],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10,
                                   env=env, shell=False)
                except (OSError, subprocess.TimeoutExpired):
                    pass
                proc.kill()
            else:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            proc.wait(timeout=10)
            rc = None
            result.update(status='FAIL', classification='timeout')
        result['attempts'].append({'returncode': rc, 'seconds': time.perf_counter() - started})
        if result['status'] == 'PASS' or result['classification'] != 'timeout':
            break
    return result
