#!/usr/bin/env python3
"""Build and exercise the wheel without importing code from the source checkout.

Requires locally installed pip, setuptools and wheel. Never installs project or
agent dependencies, uses no API, and makes no network request (--no-index).
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def checked(argv, cwd):
    result = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True, timeout=180)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)


def main(argv=None):
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    with tempfile.TemporaryDirectory() as temp:
        temp = Path(temp)
        wheels, environment, target = temp / 'wheels', temp / 'venv', temp / 'project'
        target.mkdir()
        checked([sys.executable, '-m', 'pip', 'wheel', '.', '--no-index', '--no-deps',
                 '--no-build-isolation', '--wheel-dir', str(wheels)], ROOT)
        wheel = next(wheels.glob('*.whl'))
        checked([sys.executable, '-m', 'venv', str(environment)], temp)
        windows = sys.platform == 'win32'
        python = environment / ('Scripts/python.exe' if windows else 'bin/python')
        command = environment / ('Scripts/orchestrate-toolkit.exe' if windows else 'bin/orchestrate-toolkit')
        checked([str(python), '-m', 'pip', 'install', '--no-index', '--no-deps', str(wheel)], temp)
        checked([str(command), '--help'], temp)
        for args in (['validate'], ['audit-selftest'], ['install', '--agent', 'all', '--project', str(target)],
                     ['doctor', '--project', str(target)],
                     ['uninstall', '--agent', 'all', '--project', str(target)]):
            checked([str(command)] + args, temp)
    print('Wheel smoke PASS: bundled skills validate and all adapters install/doctor/uninstall outside the checkout.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
