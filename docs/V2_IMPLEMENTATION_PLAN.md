# Universal V2 implementation plan

This plan precedes implementation. The mission explicitly asks to begin with
Sprint 1, produce the comparison and implement the first verified improvement.
Later sprints are a roadmap, not claimed deliverables of this increment.

1. Record the fresh unchanged regression baseline before writing implementation.
   Pin both repositories; record the competitor's passing selftest separately.
2. Add `benchmarks/comparison/` with independently authored fixtures and adapters.
   Use identical fixture bytes and equivalent requirements, including healthy
   Unicode/quoted input, invalid CSV, release blockers, benign source and hardcoded
   IDs. Test file discovery and installation conflict safety separately. Never
   treat a missing runtime or unsupported option as a successful check.
3. Run both pinned repositories and publish JSON plus
   `docs/COMPETITIVE_BASELINE.md`. Include missed defects and false positives,
   category denominators, process failures, runtime environment and limitations.
4. Add `orchestrate-toolkit audit-selftest`, reusing the existing contract checker.
   Require healthy controls to pass and injected defects to block; verify
   semantics-preserving transformations too. Keep this separate from workflow
   release evidence: testing an audit does not validate a participant submission.
5. Add meaningful unit/integration controls, CI selftest/report generation and
   clean-wheel coverage; update README, CHANGELOG, CONTRIBUTING and architecture.
   Run focused checks, full regressions, build smoke and comparative rerun.
6. Review preservation, commit on `codex/v2-comparative-evidence`, push and inspect
   current CI. Report measured results and unresolved limits candidly.

## Remaining sprints

Adapter support already exists; keep its live status UNKNOWN until executed in
each actual runtime. Evaluation plugins, experiment registry improvements,
evidence-linked interview answers and extended release manifests require their
own positive/negative controls and reviews. Adopt them incrementally after this
baseline identifies an actual gap. Do not rename existing commands, relax safety
checks, manufacture transcripts, or recommend changes without measurements.

## Acceptance

Existing tests pass; original skill and checker sources remain intact. Reports
show expected and actual outcomes, input fingerprints, exact revisions and
UNKNOWN/N/A reasons. A deliberately broken audit must make the new selftest fail;
healthy fixtures must remain accepted. No comparison executes fixture source,
uses paid APIs, edits challenge instructions or installs global skills.
