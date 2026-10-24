# Source-bound evidence formats

All paths inside these records are relative to the participant project. The
checker refuses traversal, linked child paths, duplicate JSON keys, nesting over
64 levels and files over 2 MiB. SHA-256 digests bind exact file bytes; line numbers are one-based. Compute
them from the actual files, not an intended future version.

## Requirement coverage

The requirements document has schema_version=1 and a requirements list. Each
entry has a unique id plus source, implementation, tests and artifacts. source is
one binding object; the other fields are lists of binding objects. A binding has
path and sha256, with an optional line. Example structure:

```json
{
  "schema_version": 1,
  "requirements": [{
    "id": "complete-output",
    "source": {"path": "problem_statement.md", "sha256": "REPLACE_WITH_ACTUAL_SHA256", "line": 1},
    "implementation": [],
    "tests": [],
    "artifacts": []
  }]
}
```

This incomplete template is intentionally not passing. Populate it from current
files. Each tests binding must reference a JSON record with exactly kind set to
test_result, status set to PASS/FAIL/UNKNOWN and subject containing a binding to
the tested implementation. A link to a test source file alone is not test evidence.
Preserve original command output alongside supplied result records for review.

Citation integrity may PASS; overall requirement satisfaction remains UNKNOWN
until independent review establishes that the implementation and test actually
cover the requirement. Failed tests and stale evidence make the report FAIL.

## Interview answers

Use schema_version=1 and an answers list. Each answer has id, question, answer,
limitations and evidence (a list of file bindings). Cite the actual implementation
and measured results used for the explanation. Missing citations remain UNKNOWN;
changed sources fail. Even fully valid citations leave factual correctness and
readiness UNKNOWN pending semantic review. This is not an official interview score.

## Behavior run metadata

Create run.json in a prepared candidate project after the actual run. Required
fields: schema_version=1, case, trial, condition (baseline or with-skill), agent,
agent_version, model, budget (a nonempty settings object), task_sha256 (from prepare),
origin (live or synthetic), and trace (project-relative normalized JSONL path).
Optional runtime_seconds and cost_usd must be finite, nonnegative measurements;
omit unavailable values rather than writing zero. Do not estimate provider cost
without supplied usage and pricing evidence.

Normalized trace events contain exactly event=read, path and sha256. Use archived
project-local copies of read skill files when the originals are elsewhere, and
document that mapping with the original export. An empty or missing trace is
UNKNOWN. A matching trace is consistency evidence only, not authenticated activation.
