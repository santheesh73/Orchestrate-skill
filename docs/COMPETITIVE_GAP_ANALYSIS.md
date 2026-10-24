# Competitive gap analysis

Reviewed 2026-10-24. Our baseline is `b77723d7e17fb95db96d654cd99530d1f72b0228`;
the competitor is `ccb175f8717f67fd084c57d853076f0b95636980` in
NITISH-R-G/hackerrank-orchestrate-skills. Its public HEAD still matches that pin.
This is a capability review, not a claim of overall superiority.

## Evidence and gaps

The tracked tree was inventoried, including the canonical skill, four companions,
ten original checkers, Python toolkit, tests, integration records and CI. Existing
release evidence is in UNIVERSAL-RELEASE-REPORT.md. Fresh regression results and
the identical-input measurements belong in COMPETITIVE_BASELINE.md.

| Area | This repository | Competitor | Priority |
|---|---|---|---|
| Contract packaging | Explicit portable contract, nonempty data, required artifacts, confined allowlist | CLI schema/enum/coverage checks, convenient complete bundle | Measure both on identical fixtures |
| Evaluator controls | Positive/negative tests distributed across unittest suite | Re-runnable selftest with injected defects and benign controls | Add public selftest using existing validators |
| Leakage | Data-driven corpus literal heuristic; questions, not proof | Production Python decision-ID heuristic; explicitly handles benign examples | Compare both; disclose different semantics and false positives |
| Installation | Ownership, conflicts, dry-run, backed-up upgrades and uninstall | Simple skill-folder copy scripts; existing same-name folders replaced | Retain existing safety; measure conflict scenario |
| Compatibility | Twelve categories with documented formats; live invocation UNKNOWN | Plain skill files and agent entry points | File discovery can be measured; activation needs real runtimes |
| Experiment memory | Existing experiment/change-record tools and guidance | Dedicated registry, Pareto analysis and reconsideration memory | Later sprint: strengthen evidence linkage rather than duplicate storage |
| Interview | Existing source/constant drill and claim audit | Adaptive interview simulator with contradiction tracking | Later sprint: artifact-bound questions and claim provenance |
| Evidence | Bound source hashes, PASS/FAIL/UNKNOWN, nine CI jobs | Findings with severity/confidence and plugin interface | Add comparison artifacts and control coverage first |

The competitor's own selftest was executed successfully: ten injected defects
caught and three benign cases quiet. These are its own controls, not an
independent comparative accuracy measurement. No third-party code is copied.

## Highest-impact first improvement

Make audit quality independently repeatable: shared healthy and defective
fixtures, raw process outcomes, exact revisions, per-category denominators,
false-positive/false-negative rates, timings and explicit UNKNOWN/N/A entries.
Expose the same contract controls through an offline toolkit selftest, backed by
positive, negative and metamorphic tests. Preserve all old skills and interfaces.

No hidden labels, live activation, actual malicious-agent behavior, official
scores or universal winner can be established by synthetic fixtures.
