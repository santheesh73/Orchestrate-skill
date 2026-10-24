"""Structured offline evaluation reusing existing strict contract and usage validators."""

import contextlib
import csv
import importlib.util
import io
import math
import time
from importlib import metadata

from .common import (ToolkitError, confined, digest, json_bytes, now, read_bytes,
                     read_json, source_root)
from .execution import run_check


def module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, source_root() / relative_path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def contract_check(root, name):
    pack = module('orchestrate_submission', 'skills/hackerrank-orchestrate-package/scripts/package_submission.py')
    path = confined(root, name)
    try:
        config, raw, sources = pack.load_contract(path)
        data = pack.snapshot(root, sources)
        with contextlib.redirect_stdout(io.StringIO()):
            # build(check_only) reuses required-file, secret and final-run hash gates.
            pack.build(root, path, '.orchestrate-contract-check-unused', check_only=True)
        return {'status': 'PASS', 'classification': 'configured_contract',
                'rows': pack.verify_csv(config, data), 'contract_sha256': digest(raw),
                'source_sha256': {n: digest(b) for n, b in data.items()}}, config, data
    except pack.Unknown:
        return {'status': 'UNKNOWN', 'classification': 'empty_data'}, None, {}
    except pack.Violation:
        return {'status': 'FAIL', 'classification': 'contract_violation'}, None, {}
    except (OSError, ValueError, csv.Error, pack.Invalid):
        return {'status': 'FAIL', 'classification': 'config_or_source_error'}, None, {}


def compare(root, first, second, id_column):
    pack = module('orchestrate_csv', 'skills/hackerrank-orchestrate-package/scripts/package_submission.py')
    a_raw, b_raw = read_bytes(confined(root, first)), read_bytes(confined(root, second))
    try:
        a_head, a_rows = pack.read_csv(a_raw, 'baseline')
        b_head, b_rows = pack.read_csv(b_raw, 'output')
        if a_head != b_head or id_column not in a_head:
            raise ToolkitError('comparison schemas differ')
        keyed = []
        for rows in (a_rows, b_rows):
            values = [r[id_column] for r in rows]
            if any(not v.strip() for v in values) or len(values) != len(set(values)):
                raise ToolkitError('comparison contains blank or duplicate IDs')
            keyed.append(dict(zip(values, rows)))
        a, b = keyed
        changes = sum(a.get(key) != b.get(key) for key in set(a) | set(b))
        return {'status': 'UNKNOWN' if not a and not b else 'PASS' if changes == 0 else 'FAIL',
                'changed_rows': changes, 'baseline_sha256': digest(a_raw), 'output_sha256': digest(b_raw),
                'classification': 'replay_comparison'}
    except (ValueError, pack.Violation) as exc:
        raise ToolkitError('invalid replay CSV') from exc


def usage(root, name, prices=None, run_id=None):
    validator = module('orchestrate_usage', 'hackerrank-orchestrate/scripts/usage_report.py')
    raw = read_bytes(confined(root, name))
    import json
    if not isinstance(prices or {}, dict):
        raise ToolkitError('prices must be a mapping of explicit input/output USD per million')
    total_in = total_out = calls = 0
    cost, unknown_cost = 0.0, False
    for line in raw.decode('utf-8').splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if validator.record_error(record):
            raise ToolkitError('invalid usage record')
        if run_id is not None and record.get('run_id') != run_id:
            continue
        calls += 1
        total_in += record['input_tokens']
        total_out += record['output_tokens']
        price = (prices or {}).get(record['model'])
        if (price is None or record.get('cache_read_input_tokens') or record.get('cache_creation_input_tokens')):
            unknown_cost = True
            continue
        if (not isinstance(price, list) or len(price) != 2
                or any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in price)):
            raise ToolkitError('prices must contain two nonnegative finite numbers')
        cost += (record['input_tokens'] * price[0] + record['output_tokens'] * price[1]) / 1_000_000
    return {'status': 'PASS' if calls else 'UNKNOWN', 'calls': calls,
            'input_tokens': total_in, 'output_tokens': total_out, 'tokens_evidence': 'MEASURED from supplied records',
            'estimated_usd': None if unknown_cost or not calls else cost,
            'cost_evidence': 'UNKNOWN' if unknown_cost or not calls else 'ESTIMATED from supplied prices',
            'sha256': digest(raw)}


def requirements(root, name):
    import re
    findings = []
    for line in read_bytes(confined(root, name)).decode('utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        match = re.fullmatch(r'([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+!-]+)', line)
        if not match:
            findings.append({'status': 'UNKNOWN', 'classification': 'unsupported_requirement_syntax'})
            continue
        try:
            actual = metadata.version(match[1])
        except metadata.PackageNotFoundError:
            actual = None
        findings.append({'package': match[1], 'status': 'PASS' if actual == match[2] else 'FAIL'})
    return {'status': worst([f['status'] for f in findings]) if findings else 'UNKNOWN', 'findings': findings,
            'note': 'Pinned-version presence only; no installation or vulnerability database lookup.'}


def worst(statuses):
    return 'FAIL' if 'FAIL' in statuses else 'UNKNOWN' if 'UNKNOWN' in statuses else 'PASS'


def evaluate(root, config_name, allow_exec=False, pass_env=()):
    start = time.perf_counter()
    config = read_json(confined(root, config_name))
    allowed = {'contract', 'authority', 'baseline', 'replay', 'checks', 'usage', 'prices',
               'run_id', 'requirements', 'estimate_text'}
    if not isinstance(config, dict) or set(config) - allowed:
        raise ToolkitError('unknown evaluation configuration keys')
    checks = {}
    contract, data = None, {}
    checks['contract'], contract, data = contract_check(root, config['contract']) if config.get('contract') else (
        {'status': 'UNKNOWN', 'classification': 'contract_not_configured'}, None, {})
    if config.get('authority'):
        checks['authority'] = {'status': 'PASS', 'sha256': digest(read_bytes(confined(root, config['authority']))),
                               'note': 'Human-supplied specification; rules were not inferred as official scores.'}
    for key in ('baseline', 'replay'):
        if config.get(key):
            if not contract:
                checks[key] = {'status': 'UNKNOWN', 'classification': 'valid_contract_required'}
            else:
                checks[key] = compare(root, config[key], contract['output'], contract['id_column'])
    # Capture all bindings before any authorized command can change them. A replay
    # alias of output must not replace its pre-command digest with a fresh value.
    bindings = {name: digest(value) for name, value in data.items()}
    for name in [config_name] + [config[k] for k in ('contract', 'authority', 'baseline', 'replay', 'usage', 'requirements', 'estimate_text') if config.get(k)]:
        bindings.setdefault(name, digest(read_bytes(confined(root, name))))
    commands = config.get('checks', [])
    if not isinstance(commands, list) or len(commands) > 50:
        raise ToolkitError('checks must be a bounded list')
    for index, command in enumerate(commands):
        checks['fixture_' + str(index + 1)] = run_check(command, root, allow_exec, pass_env)
    if config.get('usage'):
        checks['usage'] = usage(root, config['usage'], config.get('prices'), config.get('run_id'))
    if config.get('requirements'):
        checks['dependencies'] = requirements(root, config['requirements'])
    if config.get('estimate_text'):
        text = read_bytes(confined(root, config['estimate_text'])).decode('utf-8')
        checks['token_estimate'] = {'status': 'PASS', 'tokens': (len(text) + 3) // 4,
                                    'evidence': 'ESTIMATED chars/4, not a tokenizer or measured provider usage'}
    if any(digest(read_bytes(confined(root, name))) != expected for name, expected in bindings.items()):
        checks['source_stability'] = {'status': 'FAIL', 'classification': 'source_changed_during_evaluation'}
    return {'schema_version': 1, 'kind': 'evaluation', 'at': now(), 'overall': worst([c['status'] for c in checks.values()]),
            'checks': checks, 'bound_sources': bindings, 'project_id': digest(str(root).encode('utf-8')),
            'seconds': time.perf_counter() - start, 'official_score': 'UNKNOWN',
            'execution_authorized': allow_exec,
            'boundary': 'Configured checks only. No sandbox, hidden-label correctness or official score guarantee.'}
