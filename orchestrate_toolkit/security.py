"""Redacted common-credential findings and explicit, bounded file scans."""

import re
from . import records
from .common import confined, read_bytes

PATTERNS = {
    'private_key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'provider_key': re.compile(r'\bsk-[A-Za-z0-9_-]{20,}'),
    'github_token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})'),
    'aws_access_key': re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
    'credential_assignment': re.compile(r'''(?i)(?:api[_-]?key|secret|access[_-]?token|password)\s*[:=]\s*['"][^'"\n]{12,}['"]''')}


def scan_text(text):
    findings = []
    for kind, pattern in PATTERNS.items():
        for match in pattern.finditer(text):
            findings.append({'kind': kind, 'line': text.count('\n', 0, match.start()) + 1})
    return findings


def scan(root, names):
    records.sequence(names, 500)
    checks, hashes = {}, {}
    for name in names:
        raw = read_bytes(confined(root, name))
        hashes.update(records.bound(root, [name]))
        try:
            findings = scan_text(raw.decode('utf-8-sig'))
            checks[name] = {'status': 'FAIL' if findings else 'PASS', 'findings': findings,
                            'detail': 'Common-credential patterns only; matched text is never returned.'}
        except UnicodeError:
            checks[name] = {'status': 'UNKNOWN', 'detail': 'Binary/unsupported encoding not inspected for credentials.'}
    return {'schema_version': 1, 'kind': 'security_scan', 'overall': records.status(c['status'] for c in checks.values()),
            'checks': checks, 'bound_sources': hashes, 'boundary': 'No secret scanner is exhaustive; no file is executed.'}
