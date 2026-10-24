"""Bounded V4 records, current-source evidence checks and no-clobber reporting."""

import json
import math
from .common import ToolkitError, confined, digest, json_bytes, pairs, read_bytes, sha_string, write_new

STATES = ('PASS', 'WARN', 'FAIL', 'UNKNOWN')


def load(root, name):
    try:
        value = json.loads(read_bytes(confined(root, name), 2 * 1024 * 1024).decode('utf-8-sig'),
                           object_pairs_hook=pairs,
                           parse_constant=lambda token: invalid('nonfinite JSON number'))
    except RecursionError:
        raise ToolkitError('JSON nesting exceeds supported depth') from None
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        if depth > 64:
            raise ToolkitError('JSON nesting exceeds 64 levels')
        children = item.values() if isinstance(item, dict) else item if isinstance(item, list) else ()
        pending.extend((child, depth + 1) for child in children)
    return value


def invalid(message):
    raise ToolkitError(message)


def schema(value, required, optional=()):
    if not isinstance(value, dict) or set(value) - set(required) - set(optional) or set(required) - set(value):
        raise ToolkitError('missing or unsupported record fields')
    return value


def text(value):
    if not isinstance(value, str) or not value.strip():
        raise ToolkitError('nonempty text required')
    return value


def sequence(value, maximum=100):
    if not isinstance(value, list) or len(value) > maximum:
        raise ToolkitError('bounded list required')
    return value


def finite(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ToolkitError('finite number required')
    return value


def status(values):
    values = list(values)
    if any(v not in STATES for v in values):
        raise ToolkitError('unsupported evidence status')
    return 'FAIL' if 'FAIL' in values else 'UNKNOWN' if not values or 'UNKNOWN' in values else 'WARN' if 'WARN' in values else 'PASS'


def bound(root, names):
    return {name: digest(read_bytes(confined(root, name))) for name in names}


def current(root, hashes):
    if not isinstance(hashes, dict) or not hashes:
        return 'UNKNOWN'
    found = []
    for name, expected in hashes.items():
        if not sha_string(expected):
            raise ToolkitError('invalid source digest')
        path = confined(root, name)
        found.append('UNKNOWN' if not path.exists() else 'PASS' if digest(read_bytes(path)) == expected else 'FAIL')
    return status(found)


def evaluation_report(root, name):
    report = load(root, name)
    if (not isinstance(report, dict) or type(report.get('schema_version')) is not int
            or report['schema_version'] != 1 or report.get('kind') != 'evaluation'
            or report.get('project_id') != digest(str(root).encode('utf-8'))
            or not isinstance(report.get('checks'), dict) or not report['checks']):
        raise ToolkitError('expected a project-bound participant evaluation report')
    actual = status(c.get('status') if isinstance(c, dict) else None for c in report['checks'].values())
    if report.get('overall') != actual:
        raise ToolkitError('evaluation conclusion contradicts checks')
    freshness = current(root, report.get('bound_sources'))
    return report, status([actual, freshness])


def markdown(report):
    lines = ['# Local ' + str(report.get('kind', 'report')).replace('_', ' '), '',
             '**Status: ' + str(report.get('overall', 'UNKNOWN')) + '**', '']
    if 'readiness' in report:
        lines += ['Local readiness: ' + report['readiness'], '']
    for name, item in report.get('checks', {}).items():
        lines.append('- ' + str(name).replace('\n', ' ') + ': **' + item['status'] + '** — ' +
                     str(item.get('detail', item.get('classification', 'See JSON evidence.'))).replace('\n', ' '))
    lines += ['', '```json', json_bytes(report).decode('utf-8').rstrip(), '```', '',
              'Local evidence only; this is not official HackerRank judging.', '']
    return '\n'.join(lines)


def destination(root, name):
    target = confined(root, name)
    if target.exists():
        raise FileExistsError('report exists; choose a new path')
    if name:
        top = name.split('/')[0].casefold()
        if top in {'code', 'src', 'dataset', '.git', '.agents', '.claude', '.gemini', '.aws', '.ssh',
                   '.github', '.cursor', '.windsurf', '.clinerules', '.roo', '.continue'}:
            raise ToolkitError('report destination overlaps source or configuration')
        if name.casefold() in {'agents.md', 'claude.md', 'gemini.md', 'problem_statement.md'}:
            raise ToolkitError('report destination is protected')
        if name.startswith('.orchestrate/') and not name.startswith('.orchestrate/reports/'):
            raise ToolkitError('report destination overlaps owned state')
    return target


def output(root, report, name=None, format_name='json'):
    from .security import scan_text
    if scan_text(json_bytes(report).decode('utf-8')):
        raise ToolkitError('possible credential in report content; redact it before sharing')
    content = json_bytes(report) if format_name == 'json' else markdown(report).encode('utf-8')
    if name:
        target = destination(root, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        write_new(target, content)
    return content.decode('utf-8')
