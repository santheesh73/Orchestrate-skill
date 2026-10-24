#!/usr/bin/env python3
"""Cross-platform release smoke checks used after the test suite.

Failure it prevents: shell-specific CI commands hiding failed subprocesses,
UNKNOWN being mistaken for PASS, or distributing an unusable companion skill.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(args, expected=0):
    proc = subprocess.run([sys.executable, '-I', '-B'] + [str(a) for a in args],
                          cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, encoding='utf-8', errors='replace', timeout=180)
    if proc.returncode != expected:
        raise RuntimeError('%s exited %s, expected %s\n%s' %
                           (args[0], proc.returncode, expected, proc.stdout))
    return proc.stdout


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    for folder in (ROOT / 'tools', ROOT / 'hackerrank-orchestrate' / 'scripts'):
        for script in sorted(folder.glob('*.py')):
            run([script, '--help'])
    run([ROOT / 'tools/package_addons.py', '--validate-only'])
    run([ROOT / 'hackerrank-orchestrate/scripts/selfcheck.py',
         ROOT / 'tests/fixtures/project/selfcheck.json'])
    # Nonconfigured sections are deliberately UNKNOWN (exit 2), while claims
    # must be verified. Do not ignore the pipeline's exit status with tee/grep.
    report = run([ROOT / 'hackerrank-orchestrate/scripts/selfcheck.py',
                  ROOT / 'selfcheck.json'], expected=2)
    if not any(line.startswith('claims') and 'PASS' in line for line in report.splitlines()):
        raise RuntimeError('repository claims did not PASS:\n' + report)
    with tempfile.TemporaryDirectory() as temp:
        temp = Path(temp)
        run([ROOT / 'tools/package_skill.py', '--out', temp / 'dist', '--install', temp / 'core'])
        run([ROOT / 'tools/validate_skill.py', '--standalone', '--skill-dir',
             temp / 'core/hackerrank-orchestrate'])
        run([ROOT / 'tools/package_addons.py', '--all', '--out', temp / 'addons',
             '--install', temp / 'core'])
        run([ROOT / 'tools/validate_skill.py', '--standalone', '--skill-dir',
             temp / 'core/hackerrank-orchestrate'])
        run([ROOT / 'tools/footprint.py', '--summary'])
    print('Cross-platform smoke checks passed; original and companion packages validated.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
