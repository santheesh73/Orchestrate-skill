# Practice a complete failure-to-package workflow

This fictional four-request exercise uses no model, network or API key. It helps
rehearse a starter contract, a reproducible failure, a class-level repair, evidence
review, interview preparation and final packaging. It does not simulate official scores.

Run from the toolkit checkout. Read the practice AGENTS.md and problem_statement.md
first. Before rerunning, use a fresh copy of the practice directory so generated
evidence and submission directories do not collide with an earlier run.

## 1. Build and diagnose the baseline

```text
python examples/hackathon-practice/baseline.py
python hackerrank-orchestrate/scripts/preflight.py examples/hackathon-practice/output.csv --columns id,status --inputs examples/hackathon-practice/input.csv --id-col id --enum "status=ok|review"
```

The baseline intentionally drops empty requests. Expect preflight to report
missing coverage and exit 1. The failure is the exercise; do not suppress it or
call the baseline ready. Ask the design skill to explain the class of missing inputs.

## 2. Inspect the repair and verify the whole output

Compare baseline.py and solution.py. The repaired loop writes one result for
every input and applies the stated empty/whitespace rule without special-casing IDs.

```text
python examples/hackathon-practice/solution.py
python hackerrank-orchestrate/scripts/preflight.py examples/hackathon-practice/output.csv --columns id,status --inputs examples/hackathon-practice/input.csv --id-col id --enum "status=ok|review"
python examples/hackathon-practice/record_evidence.py
```

Preflight now exits 0. The record script checks all actual output cells against
this fictional policy and writes current file hashes, a test-result record,
requirement links and a sample answer under .orchestrate/practice-evidence. It
does not run the solution or fabricate a development transcript. Existing evidence
directories are refused. Preserve the real commands/output if documenting your run.

## 3. Inspect evidence and rehearse the explanation

```text
python tools/evaluate_behavior.py traceability --project examples/hackathon-practice --input .orchestrate/practice-evidence/requirements.json
python tools/evaluate_behavior.py interview --project examples/hackathon-practice --input .orchestrate/practice-evidence/answers.json
```

Expect citation_integrity=PASS and overall=UNKNOWN (exit 3). This is intentional:
file hashes do not establish semantic truth. Review whether the cited implementation
and actual output support the requirement and answer. Ask the practice skill:
"Why did the baseline miss rows, how does the repair generalize, and what does this
test fail to establish?" The exercise tests a deterministic router, not AI quality.

## 4. Check and build a local submission bundle

```text
python skills/hackerrank-orchestrate-package/scripts/package_submission.py --repo examples/hackathon-practice --contract examples/hackathon-practice/submission-contract.json --out .orchestrate/practice-submission --check-only
python skills/hackerrank-orchestrate-package/scripts/package_submission.py --repo examples/hackathon-practice --contract examples/hackathon-practice/submission-contract.json --out .orchestrate/practice-submission
```

The output directory must be new. Inspect the manifest, CSV and ZIP allowlist.
The practice code archive contains solution.py and its README; reproduction needs
the original challenge input.csv. PACKAGE BUILT is local packaging evidence, not
official acceptance. Use your actual edition's required artifacts and logging rules
for a real entry; this exercise does not create a participant chat transcript.
