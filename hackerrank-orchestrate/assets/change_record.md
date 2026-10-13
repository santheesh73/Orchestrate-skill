# Change record

Copy one block per non-trivial change. Keep them in a file inside the repo (for example `docs/changes.md`) so they show in the code and the transcript.

```
CHANGE:          one line, what changed
REQUIREMENT:     exact line in problem_statement.md or AGENTS.md this serves
CEILING:         rows this gap touches; how many are wrong because of it vs other causes
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
