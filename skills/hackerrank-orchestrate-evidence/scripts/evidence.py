#!/usr/bin/env python3
"""Offline behavior grading, paired comparisons and source-bound evidence checks.

No agent or participant code is executed. Exit 0 PASS, 1 FAIL, 2 invalid input,
3 UNKNOWN. A supplied trace is a record to review, never proof of authenticity.
Failure it prevents: stale sources or invented activation being called verified.
"""

import argparse
import csv
import hashlib
import io
import json
import math
import re
import shutil
import sys
import tempfile
from pathlib import Path

LIMIT = 2 * 1024 * 1024
STATUSES = ('PASS', 'FAIL', 'UNKNOWN')


class Invalid(ValueError):
    """Invalid or unsafe evidence configuration."""


def sha(data):
    return hashlib.sha256(data).hexdigest()


def bounded(path):
    if path.is_symlink() or not path.is_file():
        raise Invalid('expected a regular file: ' + path.name)
    with path.open('rb') as stream:
        data = stream.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise Invalid('file exceeds evidence size limit')
    return data


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise Invalid('duplicate JSON key')
        result[key] = value
    return result


def loads(data):
    try:
        value = json.loads(data, object_pairs_hook=pairs,
                           parse_constant=lambda item: fail('non-finite JSON number'))
    except RecursionError:
        raise Invalid('JSON nesting exceeds supported depth') from None
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        if depth > 64:
            raise Invalid('JSON nesting exceeds 64 levels')
        if isinstance(item, dict):
            pending.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            pending.extend((child, depth + 1) for child in item)
    return value


def fail(message):
    raise Invalid(message)


def read(path):
    return loads(bounded(path).decode('utf-8-sig'))


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode('utf-8')


def exact(obj, required, optional=()):
    if not isinstance(obj, dict) or set(obj) - set(required) - set(optional) or set(required) - set(obj):
        raise Invalid('unexpected or missing schema fields')
    return obj


def text(value):
    if not isinstance(value, str) or not value.strip():
        raise Invalid('expected nonempty text')
    return value


def safe(root, name):
    text(name)
    if '\\' in name or any(ord(c) < 32 or c in ':*?"<>|' for c in name):
        raise Invalid('expected portable relative path')
    target = root
    for part in name.split('/'):
        if part in ('', '.', '..') or part.endswith((' ', '.')):
            raise Invalid('unsafe path component')
        if part.casefold().split('.')[0] in {'con', 'prn', 'aux', 'nul'} | {
                a + str(n) for a in ('com', 'lpt') for n in range(1, 10)}:
            raise Invalid('reserved path component')
        target = target / part
        if target.is_symlink() or getattr(target, 'is_junction', lambda: False)():
            raise Invalid('linked evidence path refused')
    target.resolve().relative_to(root.resolve())
    return target


def root_path(path):
    root = Path(path).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise Invalid('expected existing project directory')
    return root


def result(items):
    values = [item['status'] for item in items]
    return 'FAIL' if 'FAIL' in values else 'UNKNOWN' if not values or 'UNKNOWN' in values else 'PASS'


def finding(name, status, detail):
    return {'name': name, 'status': status, 'detail': detail}


def case_data(suite, case_id):
    if not isinstance(case_id, str) or not re.fullmatch('[a-z][a-z0-9-]{0,63}', case_id):
        raise Invalid('invalid case ID')
    path = safe(suite, 'cases/' + case_id + '.json')
    case = exact(read(path), ('id', 'prompt', 'starter', 'expected', 'activation', 'protected', 'checks', 'manual'))
    if case['id'] != case_id or not isinstance(case['activation'], bool):
        raise Invalid('invalid case identity or activation expectation')
    text(case['prompt'])
    starter = safe(suite, case['starter'])
    expected = read(safe(suite, case['expected']))
    if not isinstance(case['checks'], list) or not case['checks']:
        raise Invalid('case requires objective checks')
    if not isinstance(case['protected'], list) or not isinstance(case['manual'], list):
        raise Invalid('invalid case lists')
    material = {'case': case, 'expected': expected, 'starter': {}}
    for item in sorted(starter.rglob('*')):
        if item.is_symlink() or getattr(item, 'is_junction', lambda: False)():
            raise Invalid('linked starter file refused')
        if item.is_file():
            material['starter'][item.relative_to(starter).as_posix()] = sha(bounded(item))
    if not material['starter']:
        raise Invalid('starter is empty')
    for name in case['protected']:
        bounded(safe(starter, name))
    names = set()
    for check in case['checks']:
        exact(check, ('name', 'type', 'path'), ('expected_key',))
        text(check['name'])
        if check['name'] in names or check['type'] not in ('csv', 'json', 'absent'):
            raise Invalid('duplicate check name or unsupported checker')
        names.add(check['name'])
        safe(starter, check['path'])
        if check['type'] != 'absent' and check.get('expected_key') not in expected:
            raise Invalid('expected data missing for check')
    for name in case['manual']:
        text(name)
    return case, expected, starter, sha(encoded(material))


def prepare(suite, case_id, out):
    """Copy only public starter files; keep expectations outside the candidate workspace."""
    case, _, starter, fingerprint = case_data(suite, case_id)
    out = Path(out).expanduser().absolute()
    # macOS uses fixed OS aliases for temporary directories; user-created links remain refused.
    if sys.platform == 'darwin':
        for name in ('var', 'tmp', 'etc'):
            alias, actual = Path('/') / name, Path('/private') / name
            if (out == alias or alias in out.parents) and alias.is_symlink() and alias.resolve() == actual:
                out = actual / out.relative_to(alias)
                break
    for parent in (out,) + tuple(out.parents):
        if parent.is_symlink() or getattr(parent, 'is_junction', lambda: False)():
            raise Invalid('linked destination refused')
    if out.exists():
        raise Invalid('destination exists; use a fresh workspace')
    # The caller chooses this output; no shell or participant program is invoked.
    shutil.copytree(starter, out)
    return {'kind': 'behavior_preparation', 'overall': 'PASS', 'case': case_id,
            'task_sha256': fingerprint, 'project': str(out.resolve()), 'prompt': case['prompt'],
            'next': 'Run the agent separately, export its genuine tool trace and create run.json using the documented schema.'}


def table(path):
    reader = csv.reader(io.StringIO(bounded(path).decode('utf-8-sig'), newline=''))
    rows = list(reader)
    if not rows or not rows[0] or len(set(rows[0])) != len(rows[0]):
        raise Invalid('empty or duplicate CSV header')
    if any(len(row) != len(rows[0]) for row in rows[1:]):
        raise Invalid('ragged CSV')
    return rows


def activation(root, trace_name, expected):
    path = safe(root, trace_name)
    if not path.exists():
        return finding('activation_record', 'UNKNOWN', 'No exported tool-read evidence; not live-verified.')
    lines = bounded(path).decode('utf-8-sig').splitlines()
    events = [loads(line) for line in lines if line.strip()]
    if not events:
        return finding('activation_record', 'UNKNOWN', 'Empty trace cannot establish non-activation.')
    skill_reads = []
    for event in events:
        exact(event, ('event', 'path', 'sha256'))
        if event['event'] != 'read':
            raise Invalid('trace accepts normalized file-read events only')
        target = safe(root, event['path'])
        if sha(bounded(target)) != event['sha256']:
            return finding('activation_record', 'FAIL', 'Exported read digest differs from archived file.')
        if target.name == 'SKILL.md' and target.parent.name.startswith('hackerrank-orchestrate'):
            skill_reads.append(event['path'])
    matches = bool(skill_reads) == expected
    return finding('activation_record', 'PASS' if matches else 'FAIL',
                   'Recorded skill reads match expectation; trace completeness/authenticity still requires independent review.'
                   if matches else 'Recorded skill reads do not match case expectation.')


def validate_metadata(value):
    meta = exact(value,
                 ('schema_version', 'case', 'trial', 'condition', 'agent', 'agent_version',
                  'model', 'budget', 'task_sha256', 'origin', 'trace'), ('runtime_seconds', 'cost_usd'))
    if type(meta['schema_version']) is not int or meta['schema_version'] != 1 or meta['condition'] not in ('baseline', 'with-skill'):
        raise Invalid('invalid run schema or condition')
    if meta['origin'] not in ('live', 'synthetic'):
        raise Invalid('origin must distinguish live from synthetic records')
    for key in ('case', 'trial', 'agent', 'agent_version', 'model', 'task_sha256', 'trace'):
        text(meta[key])
    if not isinstance(meta['budget'], dict) or not meta['budget']:
        raise Invalid('record the actual comparable budget')
    for key in ('runtime_seconds', 'cost_usd'):
        if key in meta and (type(meta[key]) not in (int, float) or not math.isfinite(meta[key]) or meta[key] < 0):
            raise Invalid('invalid optional usage measurement')
    return meta


def run_metadata(root):
    return validate_metadata(read(safe(root, 'run.json')))


def grade(suite, case_id, root):
    """Grade artifacts and supplied trace consistency, without claiming live authenticity."""
    case, expected, starter, fingerprint = case_data(suite, case_id)
    meta = run_metadata(root)
    if meta['case'] != case_id or meta['task_sha256'] != fingerprint:
        raise Invalid('run belongs to different or changed task')
    checks = []
    for name in case['protected']:
        target = safe(root, name)
        status = 'PASS' if target.is_file() and bounded(target) == bounded(safe(starter, name)) else 'FAIL'
        checks.append(finding('preserved:' + name, status, 'Compared with the starter bytes.'))
    for check in case['checks']:
        target = safe(root, check['path'])
        if check['type'] == 'absent':
            checks.append(finding(check['name'], 'PASS' if not target.exists() else 'FAIL', 'Expected artifact to be absent.'))
            continue
        if not target.is_file():
            checks.append(finding(check['name'], 'FAIL', 'Required artifact is missing.'))
            continue
        try:
            actual = table(target) if check['type'] == 'csv' else read(target)
            matches = actual == expected[check['expected_key']]
            checks.append(finding(check['name'], 'PASS' if matches else 'FAIL', 'Exact task-specific artifact comparison.'))
        except (Invalid, UnicodeError, json.JSONDecodeError, csv.Error) as exc:
            checks.append(finding(check['name'], 'FAIL', 'Malformed artifact: ' + type(exc).__name__))
    activation_expected = case['activation'] and meta['condition'] == 'with-skill'
    checks.append(activation(root, meta['trace'], activation_expected))
    checks.extend(finding(name, 'UNKNOWN', 'Requires independent semantic review of the genuine execution trace.')
                  for name in case['manual'])
    return {'schema_version': 1, 'kind': 'behavior_evaluation', 'overall': result(checks),
            'metadata': meta, 'project': str(root), 'case_sha256': fingerprint,
            'grader_sha256': sha(bounded(Path(__file__))), 'checks': checks,
            'live_verification': 'UNKNOWN',
            'limits': 'Artifact and trace consistency only; no agent was launched and no trace was authenticated.'}


def binding(root, item):
    exact(item, ('path', 'sha256'), ('line',))
    path = safe(root, item['path'])
    if not isinstance(item['sha256'], str) or not re.fullmatch('[a-f0-9]{64}', item['sha256']):
        raise Invalid('evidence binding needs a SHA-256 digest')
    if not path.exists():
        return finding(item['path'], 'UNKNOWN', 'Evidence file missing.')
    data = bounded(path)
    if sha(data) != item['sha256']:
        return finding(item['path'], 'FAIL', 'Evidence changed; citation is stale.')
    if 'line' in item:
        line = item['line']
        if type(line) is not int or line < 1 or line > len(data.decode('utf-8-sig').splitlines()):
            raise Invalid('citation line outside file')
    return finding(item['path'], 'PASS', 'Current file matches supplied hash; relevance requires review.')


def evidence_audit(root, filename, interview=False):
    """Check requirement coverage or answer citations, never infer semantic truth from links."""
    document = exact(read(safe(root, filename)), ('schema_version', 'answers' if interview else 'requirements'))
    if type(document['schema_version']) is not int or document['schema_version'] != 1:
        raise Invalid('unsupported evidence schema')
    entries = document['answers' if interview else 'requirements']
    if not isinstance(entries, list):
        raise Invalid('evidence entries must be a list')
    checks, ids = [], set()
    for entry in entries:
        if interview:
            exact(entry, ('id', 'question', 'answer', 'limitations', 'evidence'))
            for key in ('question', 'answer', 'limitations'):
                text(entry[key])
            groups = {'evidence': entry['evidence']}
        else:
            exact(entry, ('id', 'source', 'implementation', 'tests', 'artifacts'))
            groups = {'source': [entry['source']], **{key: entry[key] for key in ('implementation', 'tests', 'artifacts')}}
        ident = text(entry['id'])
        if ident in ids:
            raise Invalid('duplicate evidence ID')
        ids.add(ident)
        for group, refs in groups.items():
            if not isinstance(refs, list):
                raise Invalid('evidence references must be lists')
            if not refs:
                checks.append(finding(ident + ':' + group, 'UNKNOWN', 'No evidence supplied.'))
            for ref in refs:
                bound = binding(root, ref)
                bound['name'] = ident + ':' + group + ':' + bound['name']
                checks.append(bound)
        if not interview:
            # Test evidence must be a result record, not merely a link to test source.
            for ref in entry['tests']:
                path = safe(root, ref['path'])
                if path.is_file() and sha(bounded(path)) == ref['sha256']:
                    record = exact(read(path), ('kind', 'status', 'subject'))
                    if record['kind'] != 'test_result' or record['status'] not in STATUSES:
                        raise Invalid('test reference must identify a test_result record')
                    subject = binding(root, record['subject'])
                    checks.append(finding(ident + ':test-subject', subject['status'], subject['detail']))
                    checks.append(finding(ident + ':test-result', record['status'], 'Supplied test result; not re-executed or authenticated.'))
    integrity = result(checks)
    return {'schema_version': 1, 'kind': 'interview_citations' if interview else 'requirement_traceability',
            'overall': 'FAIL' if integrity == 'FAIL' else 'UNKNOWN', 'citation_integrity': integrity,
            'semantic_review': 'UNKNOWN', 'checks': checks,
            'limits': 'Links and hashes do not establish requirement satisfaction or factual correctness. Independent review is required.'}


def compare(paths):
    """Compare matched artifact checks; keep absent, mixed and insufficient trials visible."""
    groups, identities = {}, set()
    for path in paths:
        report = read(Path(path))
        if not isinstance(report, dict) or report.get('kind') != 'behavior_evaluation':
            raise Invalid('expected behavior evaluation report')
        meta = validate_metadata(report.get('metadata'))
        ident = (meta['case'], meta['trial'], meta['condition'])
        if ident in identities:
            raise Invalid('duplicate case/trial/condition')
        identities.add(ident)
        if report.get('overall') not in STATUSES or not isinstance(report.get('checks'), list) or not report['checks']:
            raise Invalid('invalid or empty report checks')
        names = [c.get('name') for c in report['checks']]
        if len(names) != len(set(names)) or any(c.get('status') not in STATUSES for c in report['checks']):
            raise Invalid('duplicate or invalid report check')
        if report['overall'] != result(report['checks']):
            raise Invalid('report conclusion contradicts checks')
        groups.setdefault(ident[:2], {})[meta['condition']] = report
    paired, missing = [], []
    for key, conditions in sorted(groups.items()):
        if set(conditions) != {'baseline', 'with-skill'}:
            missing.append(list(key))
            continue
        left, right = conditions['baseline'], conditions['with-skill']
        fields = ('agent', 'agent_version', 'model', 'budget', 'origin', 'task_sha256')
        if any(left['metadata'][k] != right['metadata'][k] for k in fields):
            raise Invalid('paired runs differ in model, version, budget, origin or task')
        for field in ('case_sha256', 'grader_sha256'):
            if left.get(field) != right.get(field) or not re.fullmatch('[a-f0-9]{64}', str(left.get(field))):
                raise Invalid('paired task/grader fingerprint mismatch')
        if left['case_sha256'] != left['metadata']['task_sha256']:
            raise Invalid('report case fingerprint contradicts run metadata')
        if left.get('project') == right.get('project') or not left.get('project') or not right.get('project'):
            raise Invalid('paired runs need distinct fresh project paths')
        a = {c['name']: c['status'] for c in left['checks']}
        b = {c['name']: c['status'] for c in right['checks']}
        if set(a) != set(b):
            raise Invalid('paired grader denominators differ')
        # Activation has different expected behavior across conditions; exclude it from quality gains.
        objective = [name for name in a if name != 'activation_record']
        measured = [name for name in objective if a[name] != 'UNKNOWN' and b[name] != 'UNKNOWN']
        paired.append({'case': key[0], 'trial': key[1], 'measured_checks': len(measured),
                       'unknown_checks': len(objective) - len(measured),
                       'baseline_pass': sum(a[n] == 'PASS' for n in measured),
                       'with_skill_pass': sum(b[n] == 'PASS' for n in measured),
                       'regressions': [n for n in measured if a[n] == 'PASS' and b[n] == 'FAIL'],
                       'improvements': [n for n in measured if a[n] == 'FAIL' and b[n] == 'PASS'],
                       'usage': {condition: {k: report['metadata'].get(k) for k in ('runtime_seconds', 'cost_usd')}
                                 for condition, report in conditions.items()}})
    return {'schema_version': 1, 'kind': 'behavior_comparison', 'overall': 'UNKNOWN',
            'pairs': paired, 'unpaired': missing, 'live_verification': 'UNKNOWN',
            'limits': 'Descriptive supplied-report comparison, not a causal or statistical improvement claim. Repeat trials and review genuine traces.'}


def synthetic_run(suite, case_id, out, condition='with-skill', trial='control-1'):
    """Build explicitly synthetic grader controls, never a participant transcript."""
    prepared = prepare(suite, case_id, out)
    root = root_path(out)
    case, expected, _, _ = case_data(suite, case_id)
    for check in case['checks']:
        target = safe(root, check['path'])
        if check['type'] == 'absent':
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        value = expected[check['expected_key']]
        if check['type'] == 'csv':
            buffer = io.StringIO(newline='')
            csv.writer(buffer).writerows(value)
            target.write_bytes(buffer.getvalue().encode('utf-8'))
        else:
            target.write_bytes(encoded(value))
    traced = case['protected'][0]
    if case['activation'] and condition == 'with-skill':
        traced = '.orchestrate/skills/hackerrank-orchestrate/SKILL.md'
        target = safe(root, traced)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b'SYNTHETIC CONTROL ONLY. No skill invocation occurred.\n')
    trace = {'event': 'read', 'path': traced, 'sha256': sha(bounded(safe(root, traced)))}
    safe(root, 'tool-trace.jsonl').write_bytes(encoded(trace).replace(b'\n', b'') + b'\n')
    safe(root, 'run.json').write_bytes(encoded({
        'schema_version': 1, 'case': case_id, 'trial': trial, 'condition': condition,
        'agent': 'synthetic-control', 'agent_version': 'none', 'model': 'none',
        'budget': {'model_calls': 0}, 'task_sha256': prepared['task_sha256'],
        'origin': 'synthetic', 'trace': 'tool-trace.jsonl'}))
    return root


def selftest(suite):
    """Exercise actual graders with healthy controls and separately injected defects."""
    controls = []
    cases = sorted((suite / 'cases').glob('*.json'))
    if not cases:
        raise Invalid('suite contains no cases')
    with tempfile.TemporaryDirectory(prefix='orchestrate-behavior-') as temp:
        for casefile in cases:
            case_id = casefile.stem
            root = synthetic_run(suite, case_id, Path(temp).resolve() / case_id)
            healthy = grade(suite, case_id, root)
            objective = [c for c in healthy['checks'] if c['detail'] !=
                         'Requires independent semantic review of the genuine execution trace.']
            controls.append(finding(case_id + ':healthy',
                                    'PASS' if objective and all(c['status'] == 'PASS' for c in objective) else 'FAIL',
                                    'Synthetic expected artifacts and trace; no model run.'))
            case, _, _, _ = case_data(suite, case_id)
            check = next(c for c in case['checks'] if c['type'] != 'absent')
            target = safe(root, check['path'])
            original = bounded(target)
            target.write_bytes(b'injected invalid artifact\n')
            broken = grade(suite, case_id, root)
            controls.append(finding(case_id + ':injected-output',
                                    'PASS' if broken['overall'] == 'FAIL' else 'FAIL',
                                    'Deliberately invalid artifact must fail.'))
            target.write_bytes(original)
            protected = safe(root, case['protected'][0])
            protected.write_bytes(b'injected starter mutation\n')
            broken = grade(suite, case_id, root)
            controls.append(finding(case_id + ':injected-source',
                                    'PASS' if broken['overall'] == 'FAIL' else 'FAIL',
                                    'Changed protected starter must fail.'))
    return {'schema_version': 1, 'kind': 'behavior_grader_selftest', 'overall': result(controls),
            'checks': controls, 'live_verification': 'UNKNOWN',
            'limits': 'Synthetic grader controls only. Does not measure coding-agent behavior or participant readiness.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('prepare', 'grade'):
        command = commands.add_parser(name)
        command.add_argument('--suite', required=True)
        command.add_argument('--case', required=True)
        command.add_argument('--out' if name == 'prepare' else '--project', required=True)
    for name in ('traceability', 'interview'):
        command = commands.add_parser(name)
        command.add_argument('--project', required=True)
        command.add_argument('--input', required=True)
    command = commands.add_parser('compare')
    command.add_argument('reports', nargs='+')
    command = commands.add_parser('selftest')
    command.add_argument('--suite', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'selftest':
            report = selftest(root_path(args.suite))
        elif args.command == 'prepare':
            report = prepare(root_path(args.suite), args.case, args.out)
        elif args.command == 'grade':
            report = grade(root_path(args.suite), args.case, root_path(args.project))
        elif args.command in ('traceability', 'interview'):
            report = evidence_audit(root_path(args.project), args.input, args.command == 'interview')
        else:
            report = compare(args.reports)
        print(encoded(report).decode('utf-8'), end='')
        return {'PASS': 0, 'FAIL': 1, 'UNKNOWN': 3}[report['overall']]
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, csv.Error) as exc:
        print('Evidence input refused: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
