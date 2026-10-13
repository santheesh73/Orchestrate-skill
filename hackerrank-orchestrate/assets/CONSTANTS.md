# Constants

Every tunable number, threshold, window, cap and ordering in the solution. The judge asks "why that number?"; this file is the answer. Keep the same reason in a comment beside the constant in code.

| Name | Value | Where | Provenance | Source or reason | Alternative rejected |
|---|---|---|---|---|---|
| | | `path:line` | MEASURED / SPEC / STANDARD / BOUND / JUDGEMENT | | |

Provenance labels:
- **MEASURED**: an experiment chose it. Name the losing alternative and the change record.
- **SPEC**: fixed by the problem statement or AGENTS.md. Cite the line.
- **STANDARD**: a canonical value you did not tune. Say exactly that.
- **BOUND**: derived from an external standard or a hard limit. Cite it.
- **JUDGEMENT**: reasoned, not measured. Say so.

Never write "chosen after evaluation" for a value that was not swept. A constant whose only source is a distribution read off the samples is not allowed (references/evaluation.md §1).

Check coverage with: `python scripts/interview_drill.py code/ --constants CONSTANTS.md`
