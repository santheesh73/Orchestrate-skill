"""Implementation-aware interview questions and checkable factual-claim consistency."""

import ast
import warnings
from . import evaluation, memory, records
from .common import ToolkitError, confined, digest, read_bytes


def prepare(root, code_names, evaluation_name=None, experiment_id=None):
    records.sequence(code_names, 50)
    questions, hashes, checks = [], records.bound(root, code_names), {}
    if not code_names:
        checks['implementation'] = {'status': 'UNKNOWN', 'detail': 'No implementation files supplied.'}
    drill = evaluation.module('v4_interview_drill', 'hackerrank-orchestrate/scripts/interview_drill.py')
    for name in code_names:
        path = confined(root, name)
        if path.suffix != '.py':
            checks[name] = {'status': 'UNKNOWN', 'detail': 'V4 source questions currently require explicit Python files; original drill supports more languages.'}
            continue
        source = read_bytes(path, 2 * 1024 * 1024).decode('utf-8-sig')
        from .security import scan_text
        secret_lines = {finding['line'] for finding in scan_text(source)}
        findings, _ = drill.scan_python(str(path), name)
        checks[name] = {'status': 'UNKNOWN' if any(f[0] == 'parse' for f in findings) else 'PASS',
                        'detail': 'Source parsed, not executed.'}
        for category, _, line, question in findings:
            if line in secret_lines or scan_text(question):
                question = 'A credential-like literal occurs at this source location. Remove it before sharing implementation details.'
            questions.append({'difficulty': 'advanced' if category in ('statistic', 'ordering') else 'intermediate',
                'category': category, 'question': question, 'evidence': {'path': name, 'line': max(line, 1), 'sha256': hashes[name]},
                'follow_up': 'Which measured alternative or failure case supports that decision?'})
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            try:
                tree = ast.parse(read_bytes(path).decode('utf-8-sig'))
            except (SyntaxError, ValueError, RecursionError):
                continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                questions.append({'difficulty': 'beginner', 'category': 'implementation',
                    'question': 'What does ' + node.name + ' consume, return and do when input is invalid?',
                    'evidence': {'path': name, 'line': node.lineno, 'sha256': hashes[name]},
                    'follow_up': 'Show the test or error path that supports your answer.'})
            elif isinstance(node, ast.ExceptHandler):
                questions.append({'difficulty': 'advanced', 'category': 'recovery',
                    'question': 'What failure reaches this handler, and what happens after recovery is exhausted?',
                    'evidence': {'path': name, 'line': node.lineno, 'sha256': hashes[name]},
                    'follow_up': 'Reproduce the failure without hiding a missing output row.'})
    if evaluation_name:
        report, state = records.evaluation_report(root, evaluation_name)
        hashes.update(records.bound(root, [evaluation_name]))
        checks['evaluation'] = {'status': state, 'detail': 'Current source-linked evaluation evidence.'}
        for name, check in report['checks'].items():
            questions.append({'difficulty': 'intermediate', 'category': 'evaluation',
                'question': 'What does ' + name + ' establish and what remains unmeasured? Recorded status: ' + check['status'],
                'evidence': {'path': evaluation_name, 'sha256': hashes[evaluation_name]},
                'follow_up': 'Which defect or counterfactual makes this check fail?'})
    if experiment_id:
        history = memory.history(root, experiment_id)
        name = memory.DIRECTORY + '/' + experiment_id + '.json'
        hashes.update(records.bound(root, [name]))
        questions.append({'difficulty': 'advanced', 'category': 'tradeoff',
            'question': 'Explain this experiment hypothesis, regressions and recorded decision history: ' + experiment_id,
            'evidence': {'path': name, 'sha256': hashes[name]},
            'follow_up': 'What alternative did you reject and what would make you reconsider?'})
    if len(questions) > 2000:
        raise ToolkitError('question bank exceeds bound; select fewer source files')
    return {'schema_version': 1, 'kind': 'interview_preparation', 'overall': records.status(c['status'] for c in checks.values()),
            'checks': checks, 'questions': questions, 'bound_sources': hashes,
            'official_judgment': 'UNKNOWN', 'boundary': 'Source-informed practice questions; no interview or answer quality score is inferred.'}


def check(root, answers_name, claims_name=None):
    helper = evaluation.module('v4_answer_citations', 'skills/hackerrank-orchestrate-evidence/scripts/evidence.py')
    citation_report = helper.evidence_audit(root, answers_name, True)
    checks = {'citations': {'status': citation_report['citation_integrity'],
                            'detail': 'Current citation hashes only; free-text factual correctness requires review.'}}
    hashes = records.bound(root, [answers_name])
    if claims_name:
        claims = records.schema(records.load(root, claims_name), ('claims',))
        hashes.update(records.bound(root, [claims_name]))
        for index, claim in enumerate(records.sequence(claims['claims'], 100), 1):
            if not isinstance(claim, dict):
                raise ToolkitError('claim must be an object')
            if claim.get('kind') == 'constant':
                records.schema(claim, ('kind', 'path', 'name', 'value'))
                name = claim['path']
                hashes.update(records.bound(root, [name]))
                source = read_bytes(confined(root, name), 2 * 1024 * 1024).decode('utf-8-sig')
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    try:
                        tree = ast.parse(source)
                    except (SyntaxError, ValueError, RecursionError):
                        tree = ast.Module(body=[], type_ignores=[])
                values, unsupported = [], object()
                for node in tree.body:  # Avoid confusing unrelated local scopes with a module constant.
                    if isinstance(node, (ast.Assign, ast.AnnAssign)):
                        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                        if any(isinstance(t, ast.Name) and t.id == claim['name'] for t in targets):
                            try:
                                values.append(ast.literal_eval(node.value))
                            except (ValueError, TypeError, MemoryError, RecursionError):
                                values.append(unsupported)
                state = 'UNKNOWN' if len(values) != 1 or values[0] is unsupported else 'PASS' if type(values[0]) is type(claim['value']) and values[0] == claim['value'] else 'FAIL'
            elif claim.get('kind') == 'metric':
                records.schema(claim, ('kind', 'experiment', 'phase', 'metric', 'value'))
                if claim['phase'] not in ('baseline', 'candidate'):
                    raise ToolkitError('invalid metric claim phase')
                records.finite(claim['value'])
                experiment = memory.get(root, claim['experiment'])
                actual = experiment[claim['phase']]['metrics'].get(claim['metric'])
                state = 'UNKNOWN' if actual is None else 'PASS' if actual == claim['value'] else 'FAIL'
                hashes.update(records.bound(root, [memory.DIRECTORY + '/' + claim['experiment'] + '.json']))
            else:
                raise ToolkitError('only explicit constant and metric claims can be checked automatically')
            checks['claim_' + str(index)] = {'status': state, 'detail': 'Compared an explicit factual claim with supplied source/experiment evidence.'}
    return {'schema_version': 1, 'kind': 'interview_answer_review',
            'overall': 'FAIL' if any(c['status'] == 'FAIL' for c in checks.values()) else 'UNKNOWN',
            'checks': checks, 'bound_sources': hashes, 'free_text_correctness': 'UNKNOWN',
            'boundary': 'Explicit constant/metric checks and citations supplement independent semantic review; not official judging.'}
