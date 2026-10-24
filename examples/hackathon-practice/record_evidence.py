#!/usr/bin/env python3
"""Record the actual practice output check and current citation hashes, without running the solution."""

import csv
import hashlib
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    directory = root / '.orchestrate/practice-evidence'
    if any(p.is_symlink() for p in (directory, directory.parent)):
        raise ValueError('linked evidence directory refused')
    directory.mkdir(parents=True, exist_ok=False)

    def binding(name):
        return {'path': name, 'sha256': hashlib.sha256((root / name).read_bytes()).hexdigest()}

    def write(name, value):
        path = directory / name
        with path.open('x', encoding='utf-8') as stream:
            json.dump(value, stream, indent=2)
            stream.write('\n')

    with (root / 'output.csv').open(encoding='utf-8', newline='') as stream:
        actual = list(csv.reader(stream))
    expected = [['id', 'status'], ['r1', 'ok'], ['r2', 'review'], ['r3', 'review'], ['r4', 'ok']]
    status = 'PASS' if actual == expected else 'FAIL'
    write('test-result.json', {'kind': 'test_result', 'status': status, 'subject': binding('output.csv')})
    write('requirements.json', {'schema_version': 1, 'requirements': [{
        'id': 'complete-output', 'source': binding('problem_statement.md'),
        'implementation': [binding('solution.py')],
        'tests': [binding('.orchestrate/practice-evidence/test-result.json')],
        'artifacts': [binding('output.csv')]}]})
    write('answers.json', {'schema_version': 1, 'answers': [{
        'id': 'empty-input', 'question': 'How does the implementation handle empty requests?',
        'answer': 'solution.py emits review for empty or whitespace-only requests and preserves every row.',
        'limitations': 'This checks only a fictional routing policy; it does not evaluate an AI agent.',
        'evidence': [binding('solution.py'), binding('.orchestrate/practice-evidence/test-result.json')]}]})
    print('Observed output check: ' + status + '; source links still require semantic review.')
    return 0 if status == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
