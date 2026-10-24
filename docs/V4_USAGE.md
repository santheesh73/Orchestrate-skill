# V4 usage and configuration

Run from this repository with Python 3.9+. The standard-library CLI remains
`python -m orchestrate_toolkit` or the installed `orchestrate-toolkit` command.
It deliberately does not claim the optional community toolkit's `orchestrate`
command. Existing install/evaluate/workflow commands remain available.

## First complete run

```text
python tools/v4_demo.py --project behavior-runs/v4-example
```

The directory must be new. The source-checkout demo copies the trusted bundled
offline example, actually runs it twice, saves the first output independently,
checks an injected invalid enum, records an experiment, creates questions and
completes a local release/package workflow. It uses no model, network or participant
transcript. Review records are labeled synthetic; the result is not real entry readiness.
Omit --project to use a temporary directory instead. Generated examples are ignored.

Inspect the resulting project with these implemented commands:

```text
python -m orchestrate_toolkit analyze --project behavior-runs/v4-example
python -m orchestrate_toolkit assess --project behavior-runs/v4-example --config assessment.json
python -m orchestrate_toolkit estimate --project behavior-runs/v4-example --config scoring.json
python -m orchestrate_toolkit memory show --project behavior-runs/v4-example --id synthetic-demo
python -m orchestrate_toolkit mentor --project behavior-runs/v4-example --evaluation .orchestrate/reports/evaluation.json --design DESIGN.md --experiment synthetic-demo
python -m orchestrate_toolkit interview prepare --project behavior-runs/v4-example --code main.py --evaluation .orchestrate/reports/evaluation.json --experiment synthetic-demo
python -m orchestrate_toolkit release-gate --project behavior-runs/v4-example --config release.json
python -m orchestrate_toolkit security --project behavior-runs/v4-example --file main.py
```

Analyze, estimate, mentor and memory history deliberately retain UNKNOWN/WARN
where interpretation or causal evidence is missing. Exit 0=PASS, 1=FAIL,
2=invalid/refused input, 3=WARN/UNKNOWN. Creation/restoration success is operational,
not a claim that an experiment improved quality. Add --format md for a readable
report; --report chooses a new project-relative file and never overwrites one.

## Challenge intelligence

`analyze` reads existing problem_statement.md, AGENTS.md, CLAUDE.md, GEMINI.md and
README.md by default. Repeat --source for a narrower explicit source list.
The challenge_contract JSON has schema_version, sections, bound_sources,
unknown_requirements, reviewed=false and overall=UNKNOWN. Each candidate retains
its text, category, source path, one-based line and source digest.

Categories cover objectives, inputs, outputs, required artifacts, allowed values,
paths, execution, evaluation and safety. Extraction does not establish precedence,
resolve conflicts, discover omitted requirements or execute source instructions.
Review against the actual edition and transcribe the strict packaging contract
using the existing [contract format](../skills/hackerrank-orchestrate-package/references/contract.md).

## Evaluation V2

The assess configuration requires evaluation, a path to an existing evaluation
config. Optional fields:

| Field | Shape | Check |
|---|---|---|
| inputs | List of path, columns, id_column; optional nonempty/enums | Exact input header, unique nonblank IDs, required cells and enums |
| relations | List of kind, first, second, id_column | equal_csv or different_csv keyed comparisons; counterfactual changes must preserve IDs |
| controls | List of name, config, expected, category | Expected PASS/WARN/FAIL/UNKNOWN from a preserved evaluator |
| required_checks | List of actual check names | Absent checks become UNKNOWN |

Control categories are healthy, mutation, adversarial and recovery. Controls never
execute configured commands; they test checker sensitivity and cannot replace
participant evidence. Relations can express replay, normalization invariance or
counterfactual change when you supply the appropriate outputs. They do not create
new model outputs themselves. Use positive and failing examples to validate assumptions.

The original evaluation config still defines contract, replay, baseline, usage,
dependencies and explicit local commands. assess forwards execution only with
--allow-exec; this remains host-permission execution, not an OS sandbox. Reports
bind sources, identify failure categories and include a reproduction argument array.
Read that command before executing it; report content is not execution authorization.

## Transparent estimates

estimate takes assumptions (nonempty text) and dimensions. Each dimension has
name, positive fractional weight and criterion_origin: official_published,
historical_edition, local_heuristic or unmeasured. Official/historical labels need
a source string; these labels are user-supplied provenance, not organizer verification.
Optional evidence/check selects a current participant-evaluation check.

Weights must sum to one, including unmeasured dimensions. PASS maps to 1,
WARN to 0.5 and FAIL to 0. UNKNOWN contributes no invented points. The report
shows known_weight and a possible_range; estimate stays null until all dimensions
have current evidence. Even a complete estimate is a local heuristic with WARN,
not a calibrated prediction or an official HackerRank score.

## Engineering memory

`memory create --config experiment.json` requires id, hypothesis, code_revision,
dataset (paths), sources (paths), configuration (mapping), baseline and candidate
(paths to metric records), directions and reconsideration. Metric records contain
metrics (finite numeric mapping), failures (text list) and checks (status list).
Directions map metric names to higher/lower. The revision label is supplied; actual
dataset and source hashes plus the observed Python/platform are recorded separately.

Records are new files under .orchestrate/memory. Regressions, new failures or failed
checks recommend rollback; incomplete evidence yields UNKNOWN. Improvements still
require review and comparable repeated experiments. No code is automatically reverted.

`memory decide --id NAME --config decision.json` appends a decision record with
decision=ACCEPT/REJECT/DEFER, reason and reconsideration. Hash links detect inconsistent
history. `memory show --id NAME` exports records and current-source status without
erasing historical measurements when code changes. `memory list` lists experiments;
`memory compare --first NAME --second NAME` compares stored candidate metrics only
when dataset fingerprints and metric directions match. These records are not signed.

## Mentor and interviews

mentor accepts optional --evaluation, --design and --experiment. Recommendations
reference current evidence, missing checks, design topics or past regressions.
Design-topic matching is heuristic, not an architecture grade. Predicted gain stays
UNKNOWN and advice never overrides a participant decision.

`interview prepare --code PATH` accepts repeated explicit Python files plus optional
evaluation/experiment evidence. It reuses the original source drill and adds function,
failure-handler, evaluation and tradeoff questions at three difficulty levels. It
does not execute code. Other-language source remains available through the original drill.

`interview check --answers answers.json` reuses the evidence companion's citation
format. Optional --claims claims.json accepts a claims list with either:

- kind=constant, path, name, value: compare one literal module-level Python constant.
- kind=metric, experiment, phase=baseline/candidate, metric, value: compare a stored number.

Unsupported dynamic constants stay UNKNOWN. Contradictions fail. Correct explicit
claims do not verify free-text meaning or predict interview performance.

## Release gate and workflow policy

release-gate config requires contract, evaluation, reproducibility, dependencies,
required_files and manual. The final evaluation must be current, PASS and cover
all configured mandatory sources. Required files are checked for presence/content;
include edition-required transcripts and usage reports in both the contract and
required_files. Do not add historical artifacts absent from your actual edition.

dependencies is either mode=standard-library or mode=pinned with path to a requirements
file. Pinned checks establish installed exact-version presence, not vulnerability
clearance or a full dependency lock. Standard-library scope is a supplied declaration
tied to the reproduction review, not an automatic import proof.

The reproduction evidence is a JSON object with kind=reproducibility, status,
reviewer, bound_sources, procedure and commands (argv/returncode records). Require
nonempty actual command records, successful return codes and hashes of every
mandatory final-run source. Preserve genuine output separately; this record does
not independently authenticate execution. The demo's synthetic record must never
be reused as a participant's human review.

manual is an explicit list (possibly empty) of id/evidence records. Each evidence
file has kind=manual_review, status, reviewer, requirement matching that id and
current bound_sources covering the mandatory artifacts. Semantic judgments and
official rules cannot be supplied by inferred machine claims.

The gate scans common secrets without printing matched values, emits a reproducibility
manifest and lists every blocker. Only all-PASS evidence yields local READY;
WARN/FAIL/UNKNOWN blocks it. Local READY is not organizer acceptance and does not upload.

For a new checkpoint, `workflow init --policy policy.json` accepts schema_version=1,
required_files (stage-to-path-list mapping) and release_gate (config path). File
gates establish presence/nonempty content, not semantic approval. Review requirements
before coding. VALIDATE and SUBMIT additionally rerun the release gate. A changed
policy or changed protected starter instruction blocks progress. Existing checkpoints
retain their legacy behavior and cannot silently acquire a different policy.

## Restore owned installations

After a V4 owned upgrade, install returns .orchestrate/backups/ID. Use its final ID:

```text
python -m orchestrate_toolkit restore --project ../entry --backup ID --dry-run
python -m orchestrate_toolkit restore --project ../entry --backup ID --approve-restore
```

Applying restoration requires the explicit approval flag. The current ledger must
match the backup transaction, all owned files must remain unmodified and archived
bytes must reconstruct the previous ownership state. Only owned files are restored
or removed; official root instructions, backups and participant evidence remain.
Caught write failures roll back. Sudden power loss and hostile concurrent changes
still require inspection. Pre-V4 backups lack the restore manifest and need manual recovery.
