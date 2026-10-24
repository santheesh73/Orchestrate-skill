"""Explicit weighted local estimates with evidence coverage and missing-score bounds."""

from . import records
from .common import ToolkitError


def estimate(root, config_name):
    config = records.schema(records.load(root, config_name), ('dimensions', 'assumptions'))
    records.text(config['assumptions'])
    dimensions = records.sequence(config['dimensions'], 30)
    if not dimensions:
        raise ToolkitError('score requires explicitly weighted dimensions')
    seen, rows, bindings = set(), [], records.bound(root, [config_name])
    total, observed, coverage = 0.0, 0.0, 0.0
    for item in dimensions:
        records.schema(item, ('name', 'weight', 'criterion_origin'), ('source', 'evidence', 'check'))
        name, weight = records.text(item['name']), records.finite(item['weight'])
        if name in seen or weight <= 0 or weight > 1:
            raise ToolkitError('score dimensions need unique names and positive fractional weights')
        seen.add(name)
        origin = item['criterion_origin']
        if origin not in ('official_published', 'historical_edition', 'local_heuristic', 'unmeasured'):
            raise ToolkitError('unsupported criterion provenance')
        if origin in ('official_published', 'historical_edition'):
            records.text(item.get('source'))
        total += weight
        state = 'UNKNOWN'
        if item.get('evidence'):
            report, freshness = records.evaluation_report(root, item['evidence'])
            bindings.update(records.bound(root, [item['evidence']]))
            bindings.update(report['bound_sources'])
            check = report['checks'].get(item.get('check'))
            # A stale report cannot contribute points, including when its old check passed.
            if records.current(root, report['bound_sources']) == 'PASS' and check:
                state = check['status']
        points = {'PASS': 1.0, 'WARN': 0.5, 'FAIL': 0.0}.get(state)
        if points is not None:
            observed += weight * points * 100
            coverage += weight
        rows.append({'name': name, 'weight': weight, 'status': state, 'normalized_points': points,
                     'criterion_origin': origin, 'source': item.get('source'),
                     'evidence': item.get('evidence'), 'check': item.get('check')})
    if abs(total - 1.0) > 1e-9:
        raise ToolkitError('score weights must sum to one; unknown dimensions must not be dropped')
    complete = abs(coverage - 1.0) < 1e-9
    return {'schema_version': 1, 'kind': 'local_score_estimate', 'overall': 'WARN' if complete else 'UNKNOWN',
            'basis': 'LOCAL HEURISTIC ONLY', 'official_score': 'UNKNOWN',
            'estimate': round(observed, 6) if complete else None,
            'known_weight': round(coverage, 9), 'possible_range': [round(observed, 6), round(observed + (1-coverage)*100, 6)],
            'dimensions': rows, 'assumptions': config['assumptions'], 'bound_sources': bindings,
            'mapping': {'PASS': 1, 'WARN': 0.5, 'FAIL': 0, 'UNKNOWN': None},
            'uncertainty': 'Not calibrated to the official judge. Provenance labels are supplied classifications, not organizer verification.'}
