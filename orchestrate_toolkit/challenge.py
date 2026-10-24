"""Contract-first, source-located challenge observations; prose remains unreviewed."""

import re
from .common import ToolkitError, confined, digest, read_bytes
from . import records

CATEGORIES = {
    'objectives': r'\b(objective|goal|build|task)\b',
    'input_schemas': r'\b(input|dataset|read|column|schema)\b',
    'output_schemas': r'\b(output|prediction|header|column|schema)\b',
    'required_artifacts': r'\b(submit|artifact|include|produce|write|required file)\b',
    'allowed_values': r'\b(allowed|enum|one of|must be|valid values)\b',
    'file_paths': r'[\w./-]+\.(csv|json|md|txt|py|zip)\b',
    'execution_constraints': r'\b(timeout|runtime|offline|network|dependency|reproduc|limit)\b',
    'evaluation_requirements': r'\b(test|evaluat\w*|metric|accuracy|rubric|judge)\b',
    'safety_restrictions': r'\b(must not|do not|never|secret|untrusted|injection|prohibit)\b'}


def analyze(root, sources=None):
    names = sources or [n for n in ('problem_statement.md', 'AGENTS.md', 'CLAUDE.md', 'GEMINI.md', 'README.md')
                        if confined(root, n).is_file()]
    records.sequence(names, 20)
    if not names or len(names) != len(set(names)):
        raise ToolkitError('select distinct existing specification sources')
    sections = {key: [] for key in CATEGORIES}
    hashes = records.bound(root, names)
    for name in names:
        data = read_bytes(confined(root, name), 2 * 1024 * 1024).decode('utf-8-sig')
        for line_number, line in enumerate(data.splitlines(), 1):
            if not line.strip():
                continue
            for category, pattern in CATEGORIES.items():
                if re.search(pattern, line, re.I):
                    if sum(len(items) for items in sections.values()) >= 2000:
                        raise ToolkitError('too many requirement candidates; select narrower source files')
                    from .security import scan_text
                    observed = '[REDACTED: credential-like source text]' if scan_text(line) else line.strip()
                    sections[category].append({'id': digest((name + ':' + str(line_number) + ':' + category).encode())[:16],
                        'text': observed, 'source': {'path': name, 'line': line_number, 'sha256': hashes[name]},
                        'interpretation': 'UNKNOWN'})
    return {'schema_version': 1, 'kind': 'challenge_contract', 'overall': 'UNKNOWN',
            'sections': sections, 'bound_sources': hashes, 'reviewed': False,
            'unknown_requirements': [key for key, items in sections.items() if not items] +
                                    ['Human interpretation, conflicts, completeness and current edition authority require review.'],
            'boundary': 'Verbatim source observations, not executable instructions or an automatically approved submission contract.'}
