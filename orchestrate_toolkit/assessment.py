"""Evaluation V2 composes preserved validators, explicit input schemas and relations."""

import csv
from . import evaluation, records
from .common import ToolkitError, confined, digest, read_bytes


def input_check(root, config):
    records.schema(config, ('path', 'columns', 'id_column'), ('enums', 'nonempty'))
    columns = records.sequence(config['columns'])
    if not columns or any(not isinstance(c, str) or not c for c in columns) or len(set(columns)) != len(columns):
        raise ToolkitError('input schema needs unique named columns')
    if config['id_column'] not in columns:
        raise ToolkitError('input ID column absent from schema')
    nonempty = records.sequence(config.get('nonempty', []))
    enums = config.get('enums', {})
    if not isinstance(enums, dict) or set(enums) - set(columns) or set(nonempty) - set(columns):
        raise ToolkitError('input constraints reference unknown columns')
    for values in enums.values():
        if not records.sequence(values) or any(not isinstance(v, str) for v in values):
            raise ToolkitError('enum values must be nonempty string lists')
    raw = read_bytes(confined(root, config['path']))
    pack = evaluation.module('v4_input_csv', 'skills/hackerrank-orchestrate-package/scripts/package_submission.py')
    try:
        header, rows = pack.read_csv(raw, 'input schema')
        if header != columns:
            return {'status': 'FAIL', 'classification': 'input_header'}
        ids = [row[config['id_column']] for row in rows]
        invalid = any(not key.strip() for key in ids) or len(ids) != len(set(ids))
        invalid |= any(not row[c].strip() for row in rows for c in nonempty)
        invalid |= any(row[c] not in allowed for row in rows for c, allowed in enums.items())
        return {'status': 'FAIL' if invalid else 'PASS' if rows else 'UNKNOWN',
                'classification': 'input_constraints', 'rows': len(rows), 'sha256': digest(raw)}
    except (pack.Violation, ValueError, csv.Error):
        return {'status': 'FAIL', 'classification': 'malformed_input'}


def assess(root, config_name, allow_exec=False, pass_env=()):
    config = records.schema(records.load(root, config_name), ('evaluation',),
                            ('inputs', 'relations', 'controls', 'required_checks'))
    initial = records.bound(root, [config_name])
    result = evaluation.evaluate(root, config['evaluation'], allow_exec, pass_env)
    result['engine'] = 'V4 evaluation V2'
    result['bound_sources'].update(initial)
    for index, item in enumerate(records.sequence(config.get('inputs', []), 50), 1):
        result['checks']['input_' + str(index)] = input_check(root, item)
        result['bound_sources'].update(records.bound(root, [item['path']]))
    for index, item in enumerate(records.sequence(config.get('relations', []), 50), 1):
        records.schema(item, ('kind', 'first', 'second', 'id_column'))
        if item['kind'] not in ('equal_csv', 'different_csv'):
            raise ToolkitError('unsupported relation; expected equal_csv or different_csv')
        relation = evaluation.compare(root, item['first'], item['second'], item['id_column'])
        if item['kind'] == 'different_csv' and relation['status'] != 'UNKNOWN':
            pack = evaluation.module('v4_relation_csv', 'skills/hackerrank-orchestrate-package/scripts/package_submission.py')
            _, first_rows = pack.read_csv(read_bytes(confined(root, item['first'])), 'relation first')
            _, second_rows = pack.read_csv(read_bytes(confined(root, item['second'])), 'relation second')
            same_ids = {row[item['id_column']] for row in first_rows} == {row[item['id_column']] for row in second_rows}
            relation['id_coverage_matches'] = same_ids
            relation['status'] = 'PASS' if same_ids and relation['changed_rows'] else 'FAIL'
        relation['classification'] = item['kind']
        result['checks']['relation_' + str(index)] = relation
        result['bound_sources'].update(records.bound(root, [item['first'], item['second']]))
    controls = []
    for item in records.sequence(config.get('controls', []), 30):
        records.schema(item, ('name', 'config', 'expected', 'category'))
        if item['expected'] not in records.STATES or item['category'] not in ('healthy', 'mutation', 'adversarial', 'recovery'):
            raise ToolkitError('invalid control expectation/category')
        measured = evaluation.evaluate(root, item['config'], False)
        controls.append({'name': records.text(item['name']), 'category': item['category'],
                         'expected': item['expected'], 'actual': measured['overall'],
                         'status': 'PASS' if measured['overall'] == item['expected'] else 'FAIL'})
        result['bound_sources'].update(measured['bound_sources'])
    result['control_results'] = controls
    if any(c['status'] == 'FAIL' for c in controls):
        result['checks']['control_sensitivity'] = {'status': 'FAIL', 'classification': 'unexpected_control_result'}
    for name in records.sequence(config.get('required_checks', ['contract'])):
        records.text(name)
        if name not in result['checks']:
            result['checks'][name] = {'status': 'UNKNOWN', 'classification': 'required_check_missing'}
    freshness = records.current(root, result['bound_sources'])
    if freshness != 'PASS':
        result['checks']['source_stability'] = {'status': freshness, 'classification': 'source_changed'}
    result['overall'] = records.status(c['status'] for c in result['checks'].values())
    result['reproduction'] = ['python', '-m', 'orchestrate_toolkit', 'assess', '--config', config_name]
    result['boundary'] += ' Control results measure checker sensitivity, not participant semantic quality.'
    return result
