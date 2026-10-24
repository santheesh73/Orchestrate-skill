# V4 component contracts

One canonical skill remains the entrypoint. Its activation description and all
canonical rules are retained; one on-demand reference routes to the optional CLI.
The five existing companions remain focused. No extra agent runtime or database
is required. Runtime dependencies remain Python's standard library.

| Component | Purpose | Inputs | Outputs | Failure and validation | Execution modes |
|---|---|---|---|---|---|
| Challenge Intelligence | Organize source-located obligations | Explicit spec/instruction files | challenge_contract JSON | Bound paths/bytes/lines, bounded candidates; interpretation UNKNOWN | Read-only heuristic extraction |
| Workflow Coordinator | Preserve lifecycle evidence and recovery | Checkpoint, stage evidence, optional policy | State and structured history | Source/policy hashes, valid transitions, mandatory files, PASS evidence, bounded recovery | Explicit local checkpoint mutations; no upload |
| Agent Integration | Install canonical guidance per platform | Agent ID, scope, owned ledger | Adapter files, backups, diagnostics | Conflicts/edits/links refused; transactions and explicit restore approval | Project or documented native user scope; dry-run |
| Evaluation Engine | Check configured artifacts and robustness | Existing evaluation config, input schemas, relations, controls | JSON/Markdown participant report | Required checks, fingerprints, malformed/empty/stale cases remain fail/unknown | Offline by default; existing bounded commands need consent |
| Engineering Memory | Retain reproducible experiments and decisions | Hypothesis, revisions, dataset/config/metrics | Immutable snapshots, decision chain, comparisons | No-clobber IDs, finite metrics, compatible denominators, chain consistency | Explicit local writes and read-only export |
| Engineering Mentor | Recommend evidence-backed next work | Evaluation, design, experiment history | Cited advice and uncertainty | Missing/stale evidence visible; no predicted gain | Read-only deterministic heuristics |
| Interview Intelligence | Practise the actual implementation | Python source, evaluations, experiments, answers/claims | Questions, follow-ups, consistency findings | Static inspection only; unsupported claims or unreviewed semantics remain UNKNOWN | Offline question generation and evidence checks |
| Submission Validator | Enforce the edition's local release policy | Contract, evaluation, reproduction/manual records, required files | Readiness, manifest and blockers | Every mandatory check PASS before local READY; required hashes current | Read-only gate; original explicit packager builds archives |
| Security/Reliability | Constrain local operations and redact findings | Selected files, bounded records, explicit argv | Redacted findings, refused paths, audit records | Traversal/link protection, size/depth bounds, no shell strings, timeout limits | No automatic external effect, API, package install or model launch |

## Reuse and boundaries

assessment.py wraps evaluation.py and the existing contract packager instead of
duplicating submission semantics. interview.py reuses the original source drill and
the evidence companion. Shared V4 records provide bounded JSON, current-source
validation and protected no-clobber report outputs. The original standalone evidence
companion stays self-contained rather than gaining a hidden package dependency.

Workflow gates accept participant-evaluation evidence, not selftest, mentor,
comparison or citation-only reports. Supplied human/reproduction records remain
attestations; file hashes establish consistency, not truth, authorship or actual
execution. Optional local execution has host permissions and is not an OS sandbox.

The CLI retains orchestrate-toolkit to avoid colliding with the optional community
toolkit's command. All new commands support project scoping and JSON/Markdown
reports. Installation copies canonical files; it does not rewrite official root
instructions. Existing checkpoints and checker arguments remain compatible.

See [usage and schemas](V4_USAGE.md), [audit](V4_REPOSITORY_AUDIT.md) and
[implementation plan](V4_IMPLEMENTATION_PLAN.md).
