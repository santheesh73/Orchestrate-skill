# Universal toolkit release report

Scope: 3.0.0, developed from the passing additive-skills branch. The audit and
prioritized plan were committed before implementation. Existing skills remain;
all ten original checker scripts are retained without source changes. The main
skill gains an explicitly recorded I/O/recovery addition; its fourteen rules,
trigger and core principle remain protected by the existing regression tests.

## Deliverables

| Phase | Result | Evidence / boundary |
|---|---|---|
| 1 audit | Tracked baseline inventoried and high-risk paths reviewed | UNIVERSAL-AUDIT-PLAN.md; historical findings distinguished |
| 2 architecture | Canonical source folders retained; skill contracts and capability catalog added | Existing validator and integration hash/rule tests |
| 3 adapters | Twelve documented/manual agent categories rendered | Native skills distinguished from instructions/CLI/manual |
| 4 installation | Install, doctor, validate, uninstall, dry-run, shared ownership, backup and idempotence | Lifecycle simulations; no root instruction replacement |
| 5 workflow | Explicit states, evidence-bound gates, checkpoints, bounded failure/recovery | Full synthetic route and stale-evidence tests |
| 6 evaluation | Contract, fixtures, schema, rows, replay/baseline, usage, dependency and timing reports | No hidden-label or official score claims |
| 7 security | Confined paths, ownership, consent, minimal environment and bounded execution | Negative controls; no OS sandbox guarantee |
| 8 compatibility | Adapter lifecycle and artifact tests plus clean-wheel console smoke | Live agent inference remains UNKNOWN |
| 9 developer experience | CLI, architecture, catalog, source-linked compatibility, examples and policies | Executable offline examples; legacy commands retained |
| 10 readiness | Local suite and remote matrix results recorded below | Do not infer production readiness from file generation |

## Measured validation

Local combined suite: 219 tests completed successfully on Windows Python 3.14.3,
with two platform-specific skips. Subsequent focused checks covered retained
uninstall history, shared ownership, rollback and complete canonical bundles.
All five skill folders validate; targeted static analysis reports zero errors
across 19 files. Original packaging/installation smoke checks pass. The real
console command validates and installs/doctors/uninstalls from a clean virtual
environment outside the checkout. The executable offline example passes.

The original lexical trigger proxy is unchanged: 56 cases, precision 0.76 and
recall 0.68. This is not model selection accuracy. Remote Windows/Linux/macOS
matrix verification is pending until recorded below.

The first macOS run exposed the standard /var to /private/var system-alias path
being rejected by the older companion installer. The fix normalizes only the
fixed macOS OS aliases, keeps custom symlink refusal, and has local companion
regressions plus the macOS rerun as evidence. GitHub actions were also updated
to their Node 24 versions after checking their official repositories.

Earlier focused checks: all five skill folders validated; new static checks
reported zero errors. Adapter lifecycle simulation passed for every registered
category. Source-grounded workflow, consent, usage and regression checks passed
after correcting a JSONL test fixture. The earlier wheel smoke passed outside
the source checkout; the final smoke additionally exercises the installed console
command in a clean virtual environment.

Local synthetic benchmark on this Windows host: all-agent install 15.68 seconds,
uninstall 24.74 seconds, doctor PASS, valid-contract control PASS and missing-row
control FAIL. These timings describe this host and fixture only. They do not
measure model quality or predict another machine's performance.

## Remaining limitations

- No new live inference/discovery/invocation verification in the external coding
  agents. The old single Claude Code smoke run is historical core-skill evidence.
- A documented rule format can be disabled by version, trust or UI configuration.
  Windsurf uses its documented legacy fallback; Copilot varies by surface.
- User-global installation is limited to documented native skill directories.
  Other agents have project-local/manual paths; unknown IDs are unsupported.
- No OS sandbox or network isolation. Explicitly authorized local code has host
  permissions; run unfamiliar code in a separately trusted isolated environment.
- Caught write failures roll back; sudden power loss or malicious concurrent
  filesystem edits need manual recovery. Old unowned installations are conflicts.
- Generic dependency validation checks simple pinned versions, not vulnerability
  databases. Cache-cost support stays in the original usage-report script.
- Local evidence can be forged by its owner. Hashes bind bytes, not truth,
  authorship, hidden-label accuracy, current-contract transcription or outcomes.
- No automatic uploads, pushes, deployment, paid API calls, agent launching or
  multi-agent delegation. SUBMIT records a reviewed local handoff only.

Release commands and exact evidence are kept in CLI.md, COMPATIBILITY.md and the
repository's Actions run. No unsupported agent is labeled live-verified.
