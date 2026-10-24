"""Closed registry of opt-in contract audits; never import participant source.

Selecting decision_ids declares a policy forbidding literal dataset IDs in
comparisons, mapping keys and direct lookups in the declared Python code files.
It is a narrow syntactic policy check, not proof of generalization or leakage.
"""

import ast
from pathlib import PurePosixPath

from .common import ToolkitError, digest
from .evaluation import module

DOCUMENT_SUFFIXES = {'.md', '.rst', '.txt', '.json', '.yaml', '.yml', '.toml', '.csv', '.tsv', '.lock'}


def decision_ids(config, data):
    pack = module('orchestrate_audit_csv', 'skills/hackerrank-orchestrate-package/scripts/package_submission.py')
    _, rows = pack.read_csv(data[config['input']], 'input')
    ids = {row[config['id_column']] for row in rows}
    files = [name for name in config['code_files'] if PurePosixPath(name).suffix.casefold() not in DOCUMENT_SUFFIXES]
    findings, unsupported, scanned = [], [], 0
    for name in files:
        if PurePosixPath(name).suffix.casefold() != '.py':
            unsupported.append(name)
            continue
        try:
            tree = ast.parse(data[name].decode('utf-8-sig'))
        except (SyntaxError, UnicodeError, ValueError, RecursionError):
            unsupported.append(name)
            continue
        scanned += 1
        for node in ast.walk(tree):
            candidates = []
            if isinstance(node, ast.Compare):
                candidates = [node.left] + node.comparators
            elif isinstance(node, ast.Dict):
                candidates = [key for key in node.keys if key is not None]
            elif isinstance(node, ast.Subscript):
                candidates = [node.slice]
            hits = set()
            for candidate in candidates:
                for literal in ast.walk(candidate):
                    if isinstance(literal, ast.Constant) and isinstance(literal.value, str) and literal.value in ids:
                        hits.add(literal.value)
            if hits:
                findings.append({'file': name, 'line': node.lineno,
                                 'node': type(node).__name__, 'id_sha256': sorted(digest(v.encode('utf-8')) for v in hits)})
    return {'status': 'FAIL' if findings else 'UNKNOWN' if unsupported or not scanned or not ids else 'PASS',
            'classification': 'configured_literal_decision_id_policy', 'findings': findings,
            'python_files_scanned': scanned, 'unsupported_files': unsupported,
            'boundary': 'Literal IDs only; no dataflow, dynamic construction, non-Python analysis or hidden-label guarantee.'}


REGISTRY = {'decision_ids': decision_ids}


def run(names, config, data):
    if (not isinstance(names, list) or any(not isinstance(n, str) for n in names)
            or len(names) != len(set(names)) or any(n not in REGISTRY for n in names)):
        raise ToolkitError('contract_audits must be unique built-in audit names')
    return {name: REGISTRY[name](config, data) if config else
            {'status': 'UNKNOWN', 'classification': 'valid_contract_required'} for name in names}
