# Constants

Every tunable number, threshold, window, cap and ordering in the solution. The judge asks "why that number?"; this file is the answer. Keep the same reason in a comment beside the constant in code.

| Name | Value | Where | Provenance | Source or reason | Alternative rejected |
|---|---|---|---|---|---|
| | | `path:line` | MEASURED / SPEC / STANDARD / BOUND / JUDGEMENT | | |

Provenance labels:
- **MEASURED**: picked by an experiment. Point to the change record and the value that lost.
- **SPEC**: fixed by the problem statement or AGENTS.md. Cite the line.
- **STANDARD**: a conventional default left untuned. State that plainly.
- **BOUND**: comes from an outside standard or a hard limit. Give the source.
- **JUDGEMENT**: argued from reasoning, with no measurement. Admit it.

Do not describe a value as "chosen after evaluation" unless several values were actually tried. A constant that exists only because the sample distribution suggested it is not allowed (references/evaluation.md §1).

Check coverage with: `python scripts/interview_drill.py code/ --constants CONSTANTS.md`
