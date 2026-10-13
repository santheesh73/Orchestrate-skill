# Change record

Copy one block per non-trivial change. Keep them in a file inside the repo (for example `docs/changes.md`) so they show in the code and the transcript.

```
CHANGE:          one line, what changed
REQUIREMENT:     the line it serves, quoted from problem_statement.md or AGENTS.md
CEILING:         rows the gap reaches; of those, how many it (not something else) makes wrong
CLAIM:           what will improve, and in which column
JUSTIFICATION:   the domain reason this rule should exist (never "it fixes row X")
METRIC:          label-free checks + field-level sample accuracy
BASELINE:        values before
RESULT:          values after
BLAST RADIUS:    rows changed on the FULL input set; right direction; wrong direction
COUNTERFACTUAL:  change disabled -> does the effect disappear? (paste evidence)
VERDICT:         SHIP / REJECT, per the resolution table in references/evaluation.md
```

Rejected changes stay in the file with the number that killed them.
