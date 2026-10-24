# Behavior evaluation and evidence integrity

Version 3.2 adds a fifth companion without replacing any existing skill or checker.
The source CLI is `python tools/evaluate_behavior.py`; the installed companion's
`scripts/evidence.py` has the same commands and works with the standard library.
It never launches agents, executes candidate code, calls APIs or uploads anything.

## What is measured

| Case | Domain | Objective evidence | Separate human review |
|---|---|---|---|
| clear-contract | Routing | Exact output, coverage, starter preservation | Requirements read before coding |
| conflicting-instructions | Planning | Conflict artifact and no premature output | Honest explanation and precedence handling |
| missing-rows | Routing | Complete repaired CSV | Class-level repair rather than ID-specific patch |
| prompt-injection | Retrieval | Policy-compliant decisions | No injected commands executed; grounded explanation |
| resume-development | Planning | Correct output, preserved checkpoint | Current spec checked against stale assumptions |
| unrelated-request | Near-miss | Correct ordinary-task result and recorded non-activation | Full trace completeness |
| visual-evidence | Multimodal uncertainty | Correct insufficient-evidence fallback | Image actually inspected; no invented findings |
| planning-budget | Simulation | Correct worst-balance decision | Full forecast explained |

These eight public, deliberately small cases are developmental fixtures, not a
blinded benchmark or evidence of universal generalization. In particular, one
blank-image case is not a comprehensive vision evaluation. Hold additional cases
outside development when making effectiveness claims.

Run the actual grader sensitivity controls:

```text
python tools/evaluate_behavior.py selftest --suite evals/behavior
```

Eight healthy, eight invalid-output and eight changed-starter controls must pass.
Regression tests also replace the grader with always-pass and always-fail variants
and verify that the selftest detects them. A passing selftest validates controls,
not a participant entry or live coding-agent activation.

## Run a paired experiment

From the toolkit checkout, create two fresh candidate workspaces:

```text
python tools/evaluate_behavior.py prepare --suite evals/behavior --case clear-contract --out behavior-runs/clear-baseline-1
python tools/evaluate_behavior.py prepare --suite evals/behavior --case clear-contract --out behavior-runs/clear-skill-1
python -m orchestrate_toolkit install --agent codex --project behavior-runs/clear-skill-1 --dry-run
python -m orchestrate_toolkit install --agent codex --project behavior-runs/clear-skill-1
```

The preparation output provides the task fingerprint and public prompt. Expected
answers are not copied into the candidate directory. Use fresh agent sessions
whose access is limited to the candidate project; a full toolkit checkout would
expose the public expected answers. Baseline sessions must not inherit installed
global skills or treatment conversation history. The controller must verify this.

Run the two agents separately through their real interfaces using equivalent
models, versions, tools and budgets. Record which prompt was sent and the actual
settings; retain original exports. Then create run.json in each candidate project.
Example structure (replace every descriptive value with the actual record):

```json
{
  "schema_version": 1,
  "case": "clear-contract",
  "trial": "1",
  "condition": "with-skill",
  "agent": "ACTUAL_AGENT",
  "agent_version": "ACTUAL_VERSION",
  "model": "ACTUAL_MODEL_AND_SETTINGS",
  "budget": {"max_model_calls": 20},
  "task_sha256": "FINGERPRINT_PRINTED_BY_PREPARE",
  "origin": "live",
  "trace": "tool-trace.jsonl"
}
```

For the baseline use condition=baseline. The budget is a record of the controller's
actual limit; this offline tool does not enforce it. Do not use synthetic-control
artifacts as live runs. Omit unavailable optional runtime_seconds/cost_usd rather
than recording zero.

Normalize actual exported file-read events into one compact JSON object per line:
event=read, path=project-relative archived file, sha256=actual file digest. Keep
the original export and any archive path mapping separately. The checker compares
recorded digests to archived files, not to an agent's internal state. Missing or
empty traces are UNKNOWN; complete-looking traces still need authenticity review.

After genuine runs, grade each project:

```text
python tools/evaluate_behavior.py grade --suite evals/behavior --case clear-contract --project behavior-runs/clear-baseline-1
python tools/evaluate_behavior.py grade --suite evals/behavior --case clear-contract --project behavior-runs/clear-skill-1
```

Save the JSON outputs as separate new UTF-8 report files outside candidate access.
For example, after saving them as baseline-report.json and skill-report.json:

```text
python tools/evaluate_behavior.py compare baseline-report.json skill-report.json
```

Comparison rejects duplicate trials, reused project paths, unequal models,
versions, budgets, task fingerprints, grader fingerprints and check denominators.
Unpaired trials remain visible. Activation is not counted as an improvement because
the expected behavior differs by condition. The report lists observed improvements
and regressions, plus missing measurements, while retaining overall UNKNOWN.

Repeat trials, alternate condition order and inspect genuine traces before
attributing differences to the skill. Never turn a small synthetic comparison
into a guaranteed hackathon score or a compatibility claim.

## Requirement and interview evidence

Use the [source-bound formats](../skills/hackerrank-orchestrate-evidence/references/evidence-formats.md)
to connect each requirement to the spec, implementation, test-result record and
artifact. Bind test results to current tested subjects. The
[practice exercise](HACKATHON_PRACTICE.md) generates complete examples from real
local output checks without manufacturing any participant history.

```text
python tools/evaluate_behavior.py traceability --project examples/hackathon-practice --input .orchestrate/practice-evidence/requirements.json
python tools/evaluate_behavior.py interview --project examples/hackathon-practice --input .orchestrate/practice-evidence/answers.json
```

Matching links may produce citation_integrity=PASS while overall stays UNKNOWN.
Hashes prove consistency with recorded bytes; they do not prove relevance, factual
correctness, test authenticity or requirement satisfaction. Stale sources and
reported failing tests produce FAIL. Independent review must resolve semantics.

## Exit codes and CI

0=PASS, 1=FAIL, 2=refused/invalid input, 3=UNKNOWN. Prepare and healthy selftest
normally return 0. Comparisons and citation-only reviews intentionally return 3.
Do not silence that status or describe it as passing. These report kinds cannot
replace the existing workflow's participant evaluation reports.

CI runs only synthetic offline controls and regression tests. Live agent trials
use a separately supervised session with an explicit budget. See
[LIVE_VERIFICATION.md](LIVE_VERIFICATION.md) for acceptance evidence and limits.
