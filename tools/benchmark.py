#!/usr/bin/env python3
"""Measure local adapter lifecycle and synthetic contract positive/negative controls.

Benchmarks this machine only; no agent inference, API tokens or official scores.
"""

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from orchestrate_toolkit import evaluation, installer
from orchestrate_toolkit.common import json_bytes, write_new


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, help='new report file; default stdout')
    args = parser.parse_args(argv)
    with tempfile.TemporaryDirectory() as temp:
        project = Path(temp).resolve()
        begin = time.perf_counter()
        installer.install(project, ['all'])
        install_seconds = time.perf_counter() - begin
        health = installer.doctor(project)
        begin = time.perf_counter()
        installer.uninstall(project, ['all'])
        uninstall_seconds = time.perf_counter() - begin
        (project / 'input.csv').write_text('id\n1\n', encoding='utf-8')
        (project / 'output.csv').write_text('id,status\n1,ok\n', encoding='utf-8')
        (project / 'main.py').write_text('print("synthetic")\n', encoding='utf-8')
        contract = {'input': 'input.csv', 'output': 'output.csv', 'id_column': 'id', 'columns': ['id', 'status'],
                    'require_order': False, 'code_files': ['main.py'], 'required_code_files': [],
                    'artifacts': {'output.csv': 'output.csv'}}
        (project / 'contract.json').write_bytes(json_bytes(contract))
        (project / 'evaluation.json').write_bytes(json_bytes({'contract': 'contract.json'}))
        positive = evaluation.evaluate(project, 'evaluation.json')['overall']
        (project / 'output.csv').write_text('id,status\n', encoding='utf-8')
        negative = evaluation.evaluate(project, 'evaluation.json')['overall']
        result = {'evidence': 'MEASURED local synthetic benchmark; not live runtime compatibility',
                  'install_all_seconds': install_seconds, 'uninstall_all_seconds': uninstall_seconds,
                  'doctor': health['installation'], 'positive_contract': positive, 'negative_contract': negative,
                  'official_score': 'UNKNOWN'}
        if health['installation'] != 'PASS' or positive != 'PASS' or negative != 'FAIL':
            raise RuntimeError('benchmark negative/positive control failed')
    content = json_bytes(result)
    if args.out:
        write_new(args.out, content)
    else:
        print(content.decode('utf-8'), end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
