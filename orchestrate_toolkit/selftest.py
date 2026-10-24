"""Re-runnable positive, mutation and metamorphic controls for built-in audits.

This creates synthetic files in temporary directories and reuses real validators.
No participant code, model, agent runtime or shell command is executed.
"""

import copy
import tempfile
import time
from pathlib import Path

from . import audits, evaluation
from .common import digest, json_bytes, now, source_root

INPUT = 'ticket_id,text\ncase_A12,Question\ncase_B34,Announcement\n'
OUTPUT = 'ticket_id,decision,reason\ncase_A12,reply,Direct request\ncase_B34,archive,General update\n'
FILES = {'inputs.csv': INPUT, 'output.csv': OUTPUT, 'code/main.py':
         'def decide(text):\n    return "reply" if "?" in text else "archive"\n',
         'usage.md': 'Synthetic fixture: zero calls.\n', 'log.txt': 'Synthetic test transcript.\n'}
CONTRACT = {'input': 'inputs.csv', 'output': 'output.csv', 'id_column': 'ticket_id',
            'columns': ['ticket_id', 'decision', 'reason'], 'require_order': True,
            'enums': {'decision': ['reply', 'archive']},
            'code_files': ['code/main.py', 'usage.md'], 'required_code_files': ['usage.md'],
            'artifacts': {'output.csv': 'output.csv', 'log.txt': 'log.txt'}}


def controls():
    return [
        ('contract', 'healthy', 'healthy', {}, {}),
        ('contract', 'quoted_unicode', 'metamorphic', {'output.csv': OUTPUT.replace('Direct request', '"Hello, café"')}, {}),
        ('contract', 'crlf', 'metamorphic', {'output.csv': OUTPUT.replace('\n', '\r\n')}, {}),
        ('contract', 'row_permutation_allowed', 'metamorphic', {'output.csv':
         'ticket_id,decision,reason\ncase_B34,archive,General update\ncase_A12,reply,Direct request\n'}, {'require_order': False}),
        ('contract', 'missing_row', 'injected', {'output.csv': '\n'.join(OUTPUT.splitlines()[:-1]) + '\n'}, {}),
        ('contract', 'invalid_enum', 'injected', {'output.csv': OUTPUT.replace(',reply,', ',erase,')}, {}),
        ('contract', 'extra_field', 'injected', {'output.csv': OUTPUT.replace('Direct request', 'Direct request,extra')}, {}),
        ('contract', 'missing_usage', 'injected', {'usage.md': None}, {}),
        ('contract', 'missing_transcript', 'injected', {'log.txt': None}, {}),
        ('contract', 'empty_data', 'injected', {'inputs.csv': 'ticket_id,text\n', 'output.csv': 'ticket_id,decision,reason\n'}, {}),
        ('decision_ids', 'healthy_logic', 'healthy', {}, {}),
        ('decision_ids', 'benign_assignment', 'healthy', {'code/main.py': 'probe_id = "case_A12"\n'}, {}),
        ('decision_ids', 'benign_comment', 'healthy', {'code/main.py': '# case_A12 motivated this rule.\n' + FILES['code/main.py']}, {}),
        ('decision_ids', 'benign_docstring', 'healthy', {'code/main.py': '"""case_A12 motivated this rule."""\n' + FILES['code/main.py']}, {}),
        ('decision_ids', 'unseen_probe', 'healthy', {'code/main.py': 'def probe(row):\n    return row["ticket_id"] == "case_Z99"\n'}, {}),
        ('decision_ids', 'id_branch', 'injected', {'code/main.py': 'def decide(row):\n    return row["ticket_id"] == "case_A12"\n'}, {}),
        ('decision_ids', 'id_mapping', 'injected', {'code/main.py': 'ANSWERS = {"case_A12": "reply"}\n'}, {}),
        ('decision_ids', 'id_lookup', 'injected', {'code/main.py': 'def decide(rows):\n    return rows["case_B34"]\n'}, {}),
        ('replay', 'identical', 'healthy', {'replay.csv': OUTPUT}, {}),
        ('replay', 'row_reordering', 'metamorphic', {'replay.csv': '\n'.join([OUTPUT.splitlines()[0]] + list(reversed(OUTPUT.splitlines()[1:]))) + '\n'}, {}),
        ('replay', 'changed_decision', 'injected', {'replay.csv': OUTPUT.replace(',reply,', ',archive,')}, {})
    ]


def run():
    start = time.perf_counter()
    results = []
    for audit, name, kind, overlay, changes in controls():
        config = dict(copy.deepcopy(CONTRACT), **changes)
        with tempfile.TemporaryDirectory(prefix='orchestrate-audit-control-') as temp:
            root = Path(temp).resolve()
            data = {key: value.encode('utf-8') for key, value in dict(FILES, **overlay).items() if value is not None}
            for key, raw in data.items():
                path = root / key
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            (root / 'contract.json').write_bytes(json_bytes(config))
            if audit == 'contract':
                actual = evaluation.contract_check(root, 'contract.json')[0]['status']
                # Empty evidence is UNKNOWN, but must block a release PASS.
                accepted = actual in ('FAIL', 'UNKNOWN') if name == 'empty_data' else actual == ('FAIL' if kind == 'injected' else 'PASS')
            elif audit == 'decision_ids':
                actual = audits.run(['decision_ids'], config, data)['decision_ids']['status']
                accepted = actual == ('FAIL' if kind == 'injected' else 'PASS')
            else:
                actual = evaluation.compare(root, 'replay.csv', 'output.csv', 'ticket_id')['status']
                accepted = actual == ('FAIL' if kind == 'injected' else 'PASS')
            results.append({'audit': audit, 'control': name, 'kind': kind, 'actual': actual,
                            'status': 'PASS' if accepted else 'FAIL',
                            'input_sha256': {key: digest(raw) for key, raw in data.items()},
                            'contract_sha256': digest(json_bytes(config))})
    coverage = {}
    for audit in sorted({r['audit'] for r in results}):
        rows = [r for r in results if r['audit'] == audit]
        coverage[audit] = {'healthy_controls': sum(r['kind'] != 'injected' for r in rows),
                           'injected_controls': sum(r['kind'] == 'injected' for r in rows),
                           'failed_controls': sum(r['status'] == 'FAIL' for r in rows)}
    sources = ['orchestrate_toolkit/audits.py', 'orchestrate_toolkit/evaluation.py',
               'orchestrate_toolkit/selftest.py',
               'skills/hackerrank-orchestrate-package/scripts/package_submission.py']
    # Modules are normal package files in both source and wheel installations.
    hashes = {}
    for name in sources:
        path = Path(__file__).parent / Path(name).name if name.startswith('orchestrate_toolkit/') else source_root() / name
        hashes[name] = digest(path.read_bytes())
    return {'schema_version': 1, 'kind': 'audit_selftest', 'at': now(),
            'overall': 'FAIL' if any(r['status'] != 'PASS' for r in results) else 'PASS',
            'controls': results, 'coverage': coverage, 'checker_sha256': hashes,
            'seconds': time.perf_counter() - start, 'official_score': 'UNKNOWN',
            'boundary': 'Tests the audits on synthetic controls, not submission correctness or live agents.'}
