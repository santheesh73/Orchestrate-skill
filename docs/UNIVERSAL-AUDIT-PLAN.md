# Universal toolkit audit and implementation plan

Audit baseline: `5b9b372c9cac45bf6c7933f25a5604bdbdd3c856`, 2026-10-24.
The tracked inventory covers 123 files and 31 Python files, including fixtures,
five SKILL.md files, all scripts/tools, tests, integration records and CI. Python
sources were parsed and subprocess sites inventoried; high-risk installer,
packager, evaluation, command and validation paths were reviewed directly.
Historical claims in the older audit are retained as historical evidence, not
newly rerun findings. The previous baseline suite and six CI jobs passed.

## Findings and priorities

| Priority | Finding | Decision |
|---|---|---|
| P0 | No unified installer, ownership ledger, idempotence or safe uninstall | Add a transactional, ownership-aware installer; never replace unowned files |
| P0 | Competition instructions must survive every adapter | Never generate or alter root AGENTS.md, CLAUDE.md or GEMINI.md |
| P0 | Live agent support was overstated by a shared-folder sentence in INSTALL | Replace broad claims with agent-specific source and runtime evidence |
| P0 | Existing explicit command modes inherit environment and parse shell-like strings | Preserve legacy commands; new runner uses argument arrays, minimal env and explicit execution consent |
| P1 | No resumable workflow engine or machine-readable evaluation facade | Add explicit local state transitions, hashed evidence and JSON reports |
| P1 | No fixture-level adapter/ownership test suite | Test every rendered adapter and lifecycle, distinguish simulation from live runtime |
| P1 | Skills describe workflow but lack consistent input/recovery contracts | Add concise I/O and recovery guidance without deleting skills or rules |
| P1 | Contract validation/row checks, replay and usage exist separately | Compose existing functions; reuse the hardened packager for strict contracts |
| P2 | No packaged Python CLI or wheel test | Add a separate orchestrate-toolkit entrypoint and bundled canonical resources |
| P2 | Missing contributor/security/architecture/example guides | Add small executable examples and bounded operational documentation |

No external implementation will be copied. Existing core scripts and CLI
arguments remain. Existing skill bodies retain their rules and task scope.
Optional upstream scoring remains heuristic; current specifications govern.

## Initial agent classification

This table classifies the adapter mechanism chosen for implementation. Documentation
was opened on 2026-10-24; native capabilities not selected by an adapter are not
denied. Installation simulation and live inference are separate evidence axes.

| Agent | Chosen mechanism | Activation / limitation |
|---|---|---|
| Codex | Native skill support | .agents/skills; explicit name or runtime discovery |
| Claude Code | Native skill support | .claude/skills; explicit slash skill or discovery |
| Cursor | Native instruction-file support | Scoped .mdc rule; relevance depends on runtime |
| Windsurf | Native instruction-file support | Legacy .windsurf/rules fallback; manual activation |
| GitHub Copilot | Native instruction-file support | Path-scoped instructions; feature varies by surface |
| Gemini CLI | Native skill support | .gemini/skills; approval/discovery depends on settings |
| Cline | Native instruction-file support | Dedicated .clinerules markdown rule |
| Roo Code | Native instruction-file support | Dedicated .roo/rules markdown rule |
| Continue | Native instruction-file support | YAML-frontmatter markdown under .continue/rules |
| Aider | CLI-assisted support | Explicit --read file; no automatic skill claim |
| OpenCode | Native skill support | .agents/skills alias, deduplicated with Codex |
| Other agents | Manual compatibility | Explicitly read portable adapter; no discovery claim |

Source URLs, activation instructions and runtime evidence belong in the adapter
registry and generated compatibility report. Unreviewed agent features remain
unsupported by this CLI until a documented adapter is added. User-global install
is offered only for documented native skill locations; other agents use local or
manual instructions instead of inventing global paths.

## Ordered implementation and acceptance gates

1. Audit/plan (this document): record scope, sources and gaps before code changes.
2. Architecture: preserve canonical skill folders, add concise contracts and one
   catalog. Derive adapters from source content; maintain no hand-edited copies.
3. Adapters: generate native skill copies or small rule pointers for all listed
   agents; preserve root competition files. Test path/frontmatter/pointer formats.
4. Installer: implement install, doctor, validate, uninstall, dry-run, backup and
   owned-only upgrades. Test conflicts, shared ownership, modified files, symlinks,
   malicious ledgers, rollback and idempotence before using real user folders.
5. Workflow: explicit DISCOVER through SUBMIT states, bounded recovery, JSON audit
   history, checkpoints and hashed evidence. SUBMIT records approval only; no upload.
6. Evaluation: compose strict contract checking, baseline/replay comparison, usage,
   performance and optional explicitly authorized fixture commands. UNKNOWN is not
   PASS. Reports have schema/version, error classes and source hashes.
7. Security: validate confined paths, metadata, dependencies and commands. Default
   to no command execution, no environment forwarding and no agent launching.
   Isolation is a capability to report, never an invented sandbox guarantee.
8. Compatibility: lifecycle and subprocess tests for every adapter; clean wheel
   install; Windows/Linux/macOS CI. Live inference remains UNKNOWN unless actually run.
9. Documentation: quick starts, catalog, architecture, CLI, troubleshooting,
   contribution/security policies and synthetic examples with real commands.
10. Release: run old/new suites and metadata/static/security checks; generate an
    evidence-based report, commit in reviewable increments and verify branch CI.

CLI name: `orchestrate-toolkit` or `python -m orchestrate_toolkit`. The optional
community package already owns `orchestrate`; do not shadow it. Basic use is offline,
single-agent, standard-library Python. Installing the package may require a local
build backend; no paid API is needed. No command automatically pushes, deploys,
uploads, starts remote agents or enables multi-agent execution.

## Known boundaries to retain in the final report

Generated files do not prove live discovery/invocation. Local command execution is
not a sandbox. Source/member hashes do not prove output correctness. Contract
transcription and human reasoning need review. Hidden labels and official scores
are unavailable. Current challenge rules can differ from historical guidance.
