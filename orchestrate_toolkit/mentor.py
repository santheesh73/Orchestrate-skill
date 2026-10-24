"""Optional deterministic mentoring from current reports, designs and experiment history."""

import re
from . import memory, records
from .common import confined, read_bytes


def review(root, evaluation_name=None, design_name=None, experiment_id=None):
    recommendations, checks, bindings = [], {}, {}
    if evaluation_name:
        report, state = records.evaluation_report(root, evaluation_name)
        bindings.update(records.bound(root, [evaluation_name]))
        bindings.update(report['bound_sources'])
        checks['evaluation_evidence'] = {'status': state, 'detail': 'Current participant evaluation and its source bindings.'}
        for name, check in report['checks'].items():
            if check['status'] != 'PASS':
                recommendations.append({'priority': 'high' if check['status'] == 'FAIL' else 'review',
                    'action': 'Reproduce and resolve ' + name + ' before claiming this check is satisfied.',
                    'evidence': {'path': evaluation_name, 'sha256': bindings[evaluation_name], 'check': name},
                    'status': check['status'], 'expected_gain': 'UNKNOWN'})
        if 'replay' not in report['checks']:
            recommendations.append({'priority': 'review', 'action': 'Add an independent rerun/replay comparison; output shape alone does not establish repeatability.',
                                    'evidence': {'path': evaluation_name, 'sha256': bindings[evaluation_name]}, 'expected_gain': 'UNKNOWN'})
    if design_name:
        data = read_bytes(confined(root, design_name)).decode('utf-8-sig')
        bindings.update(records.bound(root, [design_name]))
        missing = [topic for topic in ('alternative', 'failure', 'uncertainty', 'test')
                   if not re.search(topic, data, re.I)]
        checks['architecture_review'] = {'status': 'WARN' if missing else 'UNKNOWN',
            'detail': 'Design topic presence is a heuristic, not architecture-quality verification.', 'missing_topics': missing}
        if missing:
            recommendations.append({'priority': 'review', 'action': 'Review design tradeoffs and missing topics: ' + ', '.join(missing),
                'evidence': {'path': design_name, 'sha256': bindings[design_name]}, 'expected_gain': 'UNKNOWN'})
    if experiment_id:
        history = memory.history(root, experiment_id)
        experiment = history['experiment']
        name = memory.DIRECTORY + '/' + experiment_id + '.json'
        bindings.update(records.bound(root, [name]))
        checks['experiment_context'] = {'status': history['current_source_status'],
                                       'detail': 'Past measurements are not re-executed; current-source status is separate.'}
        recommendations.append({'priority': 'high' if experiment['recommendation'] == 'ROLLBACK_RECOMMENDED' else 'review',
            'action': 'Review regressions and consider rollback.' if experiment['recommendation'] == 'ROLLBACK_RECOMMENDED' else
                      'Repeat the proposed experiment and test an ablation before attributing gains.',
            'evidence': {'path': name, 'sha256': bindings[name]}, 'expected_gain': 'UNKNOWN',
            'reconsideration': experiment['reconsideration'], 'recorded_decisions': len(history['decisions'])})
    if not recommendations:
        recommendations.append({'priority': 'review', 'action': 'Supply a current evaluation, written design or experiment; no gain can be estimated without evidence.',
                                'evidence': None, 'expected_gain': 'UNKNOWN'})
    return {'schema_version': 1, 'kind': 'engineering_mentor', 'overall': 'UNKNOWN', 'checks': checks,
            'recommendations': recommendations, 'bound_sources': bindings,
            'boundary': 'Heuristic advice for human review; no measurement prediction, autonomous override or participant-code execution.'}
