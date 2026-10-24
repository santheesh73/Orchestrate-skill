# V4 repository audit

Audit date: 2026-10-24. Own baseline revision:
76c928eedce69fb62cc33a81c18349d37b14b53f (version 3.2.0).
Reference revision: ccb175f8717f67fd084c57d853076f0b95636980, confirmed against
the reference repository's remote HEAD on the audit date. Reference source was
read without changing its checkout. No implementation is imported.

## Inventory and baseline

The baseline tracks 228 files, including 58 Python files. The audit read tracked
file bytes and inventoried Python symbols, references, skills, configuration,
fixtures, tests and notices. Generated build directories are not source authority.
The unchanged 228-file baseline was frozen before implementation. Its complete
regression run passed: 262 tests in 479.045 seconds, two platform-specific skips.
The snapshot was fingerprinted independently while implementation proceeded in
the main checkout. An earlier interrupted run is not counted as successful.

## Existing architecture and reusable components

| Area | Existing implementation | V4 action |
|---|---|---|
| Canonical skill | Core playbook, unchanged activation description, ten checkers | Add one progressive-disclosure V4 reference; preserve rules and scripts |
| Integration | Twelve adapter IDs, native/rule/manual routes, executable detection | Preserve mechanisms; add explicit owned-backup restoration |
| Installer | Hash ownership, no-clobber conflicts, upgrade backup, rollback, uninstall | Existing backups lack a complete, user-invocable restore transaction |
| Workflow | Nine states, checkpoint hashes, bounded recovery, local approval | Add opt-in edition policy and mandatory release checks without breaking legacy checkpoints |
| Evaluation | Contract packager reuse, keyed replay, usage, dependency presence, closed audits | Add input schemas, relation checks, defect controls and readable reports |
| Behavior evidence | Eight cases, 24 controls, paired comparisons, citations | Preserve as a distinct evidence kind; do not count selftests as participant readiness |
| Experiments | Original baseline/finish change records | Add immutable JSON registry, context fingerprints and append-only decisions |
| Interview | Source-derived drill and citation-only checks | Add difficulty, experiment-aware questions and explicitly checkable factual claims |
| Packaging | Explicit contract, safe archive members, manifest, secrets checks | Add a unified local release gate including evaluation, reproducibility and manual evidence |
| CI/distribution | Three OS x three Python versions, installed-copy and wheel smoke | Add V4 regressions and reproducible documentation checks; retain existing checks |

## Gaps and boundaries

- No structured challenge-analysis JSON interface; current extraction is a heuristic
  checklist. Prose ambiguity must remain UNKNOWN rather than becoming an inferred enum.
- No unified estimate with explicit evidence coverage and missing-dimension bounds.
- No local experiment registry binding dataset, configuration, environment and decisions.
- No implemented evidence-driven mentor beyond guidance and individual checkers.
- The existing workflow protects AGENTS/CLAUDE/spec but omits GEMINI checkpointing.
- Supplied reports and traces are not authenticated; hashes do not prove semantics.
- Arbitrary authorized code retains host permissions; the runner is not a sandbox.
- The local host blocked generated console launchers through Application Control;
  hosted 3.2 CI passed all nine configurations. Do not silently bypass host policy.
- Current universal-adapter live activation remains UNKNOWN. Documentation and
  filesystem tests must not be upgraded to live verification.
- Runtime standard-library constraints and Python 3.9 compatibility remain important.

## Source-based comparison

| Capability | Own baseline source | Reference source | What the evidence establishes |
|---|---|---|---|
| Safe install lifecycle | orchestrate_toolkit/installer.py | scripts/install-skills.ps1 and .sh | Own refuses modified/unowned outputs; reference installer documents replacing matching skill folders |
| Evaluation | orchestrate_toolkit/evaluation.py | orchestrate_kit/evaluator/runner.py | Both implement local checks; equivalence and detection rates require identical fixtures |
| Engineering memory | Original experiment.py, no general registry | orchestrate_kit/memory/store.py and experiment/store.py | Reference has searchable JSON memory and experiment storage; this is an own-baseline gap |
| Mentor | Skill guidance only | orchestrate_kit/mentor/engine.py | Reference has an executable mentor component; V4 needs working local evidence rules |
| Scoring | Guided self-score, no equivalent combined CLI estimate | orchestrate_kit/score/scoreboard.py | Reference assembles local signal estimates; estimates are not official scores |
| Release validation | Strict explicit-contract packager | skills/orchestrate-package/scripts/package_submission.py | Both check artifacts; own uses an explicit archive allowlist and supplied contract |
| Skill behavior | evals/behavior and evidence companion | Skill instructions and reference tests | No comparable genuine live-agent trials were supplied for either repository |

These are source observations, not a quality ranking. Full reference unit tests,
live activation, documentation usability with participants and hidden-grader
performance are not established by this audit. The existing independently authored
benchmark will be rerun against the exact reference revision with identical input
fingerprints, false-positive/negative denominators and explicit UNKNOWN/N/A cases.

## Identity and licensing

The project is independently maintained by SANTHEESH, under its existing MIT
license, with THIRD_PARTY_NOTICES.md preserved. The reference is comparison
material, not a source of copied implementation. Current organizer instructions
override historical May scoring, September formats and community recommendations.
