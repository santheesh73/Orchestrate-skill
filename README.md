# HackerRank Orchestrate Skills & Offline Toolkit

[![validate](https://github.com/santheesh73/Orchestrate-skill/actions/workflows/validate.yml/badge.svg?branch=main)](https://github.com/santheesh73/Orchestrate-skill/actions/workflows/validate.yml)

**Version 3.1.0 · Python 3.9+ · Standard-library runtime · MIT**

An independent toolkit for planning, building, checking and explaining a
HackerRank Orchestrate submission. It combines a core playbook, four companion
skills, ten original checker scripts and an offline Python CLI. Use it with your
coding agent to turn current challenge requirements into a design, iterate with
evidence, check artifacts and prepare for the judge interview.

The core principle is **model describes, code decides**: separate model
observations from the tested code that produces final decisions. The canonical
[skill instructions and hard rules](hackerrank-orchestrate/SKILL.md) remain the
playbook's source of truth. Existing skills and checker interfaces are preserved.

> **Your edition's challenge statement and starter instructions take precedence.**
> This community project is not affiliated with HackerRank. Passing these checks
> does not establish hidden-label accuracy, an official score or permission to
> submit. The original strategy and historical scoring context are preserved in
> the [hackathon field guide](docs/HACKATHON_GUIDE.md).

## Start here

- [Quick start](#quick-start)
- [The five skills](#the-five-skills)
- [Coding-agent compatibility](#coding-agent-compatibility)
- [Hackathon workflow](#hackathon-workflow)
- [Offline walkthrough and evaluation](#offline-walkthrough-and-evaluation)
- [Commands and original checkers](#commands-and-original-checkers)
- [Verified results](#verified-results)
- [Readiness and limits](#readiness-and-limits)
- [Documentation and repository layout](#documentation-and-repository-layout)
- [Development](#development)
- [License and credits](#license-and-credits)

## Quick start

Install Python 3.9 or newer and clone this repository. The CLI runs directly from
the checkout; its runtime needs no third-party packages or API key.

```text
git clone https://github.com/santheesh73/Orchestrate-skill.git
cd Orchestrate-skill
python -m orchestrate_toolkit validate
python -m orchestrate_toolkit audit-selftest
```

Use an **existing official challenge checkout** as the target project. The next
commands assume it is a sibling folder named `my-entry`; replace that path with
yours. Run these commands from this toolkit's repository root.

```text
python -m orchestrate_toolkit install --agent codex --project ../my-entry --dry-run
python -m orchestrate_toolkit install --agent codex --project ../my-entry
python -m orchestrate_toolkit doctor --project ../my-entry
python -m orchestrate_toolkit compatibility --project ../my-entry
```

Choose an agent ID from the table below. Repeat `--agent` for selected agents, or
use `--agent all` by itself for all project-local adapters. Installation copies
canonical skills and generates agent files. It does not launch your agent or
prove that the skills loaded.

Open your coding agent **in the challenge project**. Ask it to identify the exact
installed `hackerrank-orchestrate/SKILL.md` path, read the current starter rules
and propose the next contract check. Confirm that path in its tool evidence. Try
an unrelated request too, to check accidental activation.

Optional package installation:

```text
python -m pip install .
orchestrate-toolkit --help
```

The command is `orchestrate-toolkit`; the optional community project's
`orchestrate` command is separate. Package builds may fetch build dependencies.
The checkout-based runtime checks above work offline after cloning.

### Safe installation lifecycle

The universal installer refuses unowned files and user-modified installed files.
Unchanged installs are idempotent. An owned upgrade needs `--upgrade` and creates
a backup. Root `AGENTS.md`, `CLAUDE.md` and `GEMINI.md` are not adapter outputs.
Earlier installation tools remain available; their files are not silently
adopted by the ownership-aware installer.

```text
python -m orchestrate_toolkit install --agent codex --project ../my-entry --upgrade
python -m orchestrate_toolkit uninstall --agent codex --project ../my-entry --dry-run
python -m orchestrate_toolkit uninstall --agent codex --project ../my-entry
```

Uninstall removes unchanged owned files while preserving edits, shared files,
backups and workflow evidence. For user-scope paths, conflict recovery, legacy
commands and Claude.ai ZIP upload, see [INSTALL.md](docs/INSTALL.md) and the
[CLI reference](docs/CLI.md).

## The five skills

| Skill | Use it for | Instructions |
|---|---|---|
| `hackerrank-orchestrate` | Main playbook: starter contract, architecture, iteration, output checks and interview preparation | [Core](hackerrank-orchestrate/SKILL.md) |
| `hackerrank-orchestrate-design` | An evidence-based `DESIGN.md`, model/code boundary, failure handling and validation plan | [Design](skills/hackerrank-orchestrate-design/SKILL.md) |
| `hackerrank-orchestrate-package` | Validate an explicit submission contract and build a fresh bundle with hashes | [Packaging](skills/hackerrank-orchestrate-package/SKILL.md) |
| `hackerrank-orchestrate-practice` | Rehearse answers against actual code, constants, experiments and run evidence | [Practice](skills/hackerrank-orchestrate-practice/SKILL.md) |
| `hackerrank-orchestrate-toolkit` | Use the optional community evaluator, engineering memory and heuristic review tools | [Integration](skills/hackerrank-orchestrate-toolkit/SKILL.md) |

The community integration is optional. The other skills and original checkers
remain usable without that external project. References load on demand; the
toolkit does not maintain a separate playbook for each coding agent.

Example requests after loading the relevant skill:

```text
Read this edition's starter rules and problem statement. Help me design the agent
and identify which artifact checks we need before implementation.

Review my output and experiment record. Identify the weakest evidence and
propose one measured improvement.

Prepare interview questions from my code and constants. Mark answers that cannot
be verified from the supplied artifacts as UNKNOWN.
```

## Coding-agent compatibility

The registry covers twelve agent IDs through different mechanisms. Documented
formats and simulated installation tests do **not** establish current live
activation. The [full compatibility matrix](docs/COMPATIBILITY.md) records paths,
activation procedures, documentation sources and version-specific caveats.

| Mechanism selected by this toolkit | Agents | CLI IDs |
|---|---|---|
| Documented native skill folders | OpenAI Codex, Claude Code, Gemini CLI, OpenCode | `codex`, `claude`, `gemini`, `opencode` |
| Documented instruction/rule files | Cursor, Windsurf, GitHub Copilot, Cline, Roo Code, Continue | `cursor`, `windsurf`, `copilot`, `cline`, `roo`, `continue` |
| Explicit CLI-assisted loading | Aider | `aider` |
| Explicit manual reading | Other instruction-capable agents | `portable` |

All twelve adapters have filesystem/lifecycle test coverage. Current live
discovery and invocation remain **UNKNOWN**. The earlier one-run Claude Code
smoke test covered the original core only. Antigravity and Claude.ai have legacy
instructions in [INSTALL.md](docs/INSTALL.md), not dedicated universal CLI IDs.
For Aider, explicitly load the main skill and selected references; a routing note
alone does not load them automatically.

## Hackathon workflow

1. **Discover the contract.** Read the actual starter files, extract requirements
   and confirm logging and required artifacts. Use the
   [starter-contract reference](hackerrank-orchestrate/references/starter-contract.md).
2. **Design and build.** Choose the problem shape, write the model/code boundary
   and produce a complete sample run. Use the design companion and
   [architecture references](hackerrank-orchestrate/references/archetypes/index.md).
3. **Test and improve.** Validate rows, malformed inputs and evidence; compare
   complete outputs and keep a measured change record. Follow the
   [evaluation policy](hackerrank-orchestrate/references/evaluation.md).
4. **Rehearse and package.** Generate questions from your own source, check final
   artifacts and build a fresh submission bundle from the actual contract.

The CLI records an explicit resumable workflow:

```text
DISCOVER → ANALYZE → PLAN → BUILD → TEST → EVALUATE → IMPROVE → VALIDATE → SUBMIT
```

These are explicit transitions, not an autonomous build loop. Evidence gates
check report/source hashes; failed or stale evidence blocks progress. `IMPROVE`
can return to `BUILD` or `TEST`. `SUBMIT` records an explicitly approved local
handoff and does not upload anything. See [workflow commands](docs/CLI.md).

## Offline walkthrough and evaluation

Run from the repository root:

```text
python examples/offline/main.py
python -m orchestrate_toolkit evaluate --project examples/offline --config evaluation.json --report evaluation/readme-demo-001.json
python -m orchestrate_toolkit workflow init --project examples/offline
```

The synthetic example checks its configured CSV contract and keyed replay
without a model, API key or network. Use a new report filename for another run.
Its data and contract are not a real submission. See the
[walkthrough](examples/offline/README.md).

For your project, transcribe its current specification into an explicit contract
using the [contract reference](skills/hackerrank-orchestrate-package/references/contract.md).
The packager checks required files, exact CSV schema, IDs, enums, nonempty data,
archive scope and configured hashes. It prints `PACKAGE BUILT`, not an official
readiness verdict. The output directory must be new.

### Optional literal-ID decision audit

Add this field to an evaluation configuration when the policy should forbid
literal input IDs in Python decision logic:

```json
{
  "contract": "contract.json",
  "contract_audits": ["decision_ids"]
}
```

The audit reads IDs from the configured input and inspects comparisons, mapping
keys and direct lookups in declared Python files. Comments, docstrings, isolated
assignments and unseen probe IDs do not trigger this narrow policy. Unsupported
source yields UNKNOWN; dynamic dataflow is outside its coverage. The original
broader `corpus_literals.py` scanner remains available for investigation.

## Commands and original checkers

Run `python -m orchestrate_toolkit COMMAND --help` for exact flags.

| CLI command | Purpose |
|---|---|
| `install` / `uninstall` | Preview or manage owned project/user-scope skill installations |
| `doctor` / `compatibility` | Check installed ownership and report documented adapter capabilities |
| `validate` | Validate all canonical skill folders |
| `audit-selftest` | Check the audits using healthy, injected and metamorphic controls |
| `evaluate` | Produce evidence for configured contract, replay, checks, usage and dependencies |
| `workflow` | Initialize, inspect, advance or explicitly recover an evidence-gated checkpoint |

Every original checker remains in `hackerrank-orchestrate/scripts/`:

| Script | Purpose |
|---|---|
| `selfcheck.py` | Aggregate configured checks; missing evidence stays UNKNOWN |
| `contract_extract.py` | Extract and compare starter requirements as a reading aid |
| `check_log.py` | Check the selected log-format profile and harness naming |
| `preflight.py` | Check CSV schema, IDs, enums, blanks and distribution hints |
| `rerun_diff.py` | Compare complete outputs by ID |
| `experiment.py` | Record baseline/final checks, output changes and evidence-based verdicts |
| `usage_report.py` | Summarize supplied call records and explicitly supplied prices |
| `interview_drill.py` | Generate source-linked questions and constants checks |
| `corpus_literals.py` | Flag dataset literals in source for investigation |
| `claim_audit.py` | Compare supported documentation counts with available artifacts |

Exit-code conventions differ; inspect each script's `--help` before automating
it. These checkers are not themselves the participant's competition solution.

## Verified results

The suite contains **231 tests**. CI covers Windows, Linux and macOS with Python
3.9, 3.11 and 3.13: **nine configurations**. At revision `72f4981`, all eighteen
checks across the push and pull-request runs passed. See the
[push run](https://github.com/santheesh73/Orchestrate-skill/actions/runs/40066689590)
and [pull-request run](https://github.com/santheesh73/Orchestrate-skill/actions/runs/40066693106).
This is pinned historical evidence; the badge links to subsequent main-branch runs.

- **Audit controls:** seven healthy examples, ten injected defects and four
  metamorphic checks. Deliberately broken-checker regressions prove the selftest
  can reject an audit that always passes or always fails.
- **Installation and packaging:** conflicts, ownership, shared files, rollback,
  backups and clean-wheel operation outside the checkout are exercised.
- **Trigger evaluation:** the existing offline lexical proxy measures precision
  0.76 and recall 0.68 over its 56 prompts. It is not live model behavior.

The independent comparison uses identical synthetic inputs and requirements.
For common supported interfaces:

| Shared fixture check | This toolkit with optional `decision_ids` | Reviewed community toolkit |
|---|---|---|
| Packaging defects blocked | 12/12 | 10/12 |
| Healthy packages accepted | 4/4 | 4/4 |
| Literal-ID decision defects detected | 3/3 | 2/3 |
| Benign source cases kept quiet | 5/5 | 4/5 |

Unsupported policies are N/A and excluded from common-interface denominators;
unexecuted checks are UNKNOWN. These small, known fixtures do not establish
overall superiority, real-world error rates or competition scores. The broader
original scanner has a different purpose and flags one benign fixture under the
narrow policy. Read the [full comparison](docs/COMPETITIVE_BASELINE.md),
[reports and reproduction instructions](benchmarks/comparison/README.md), and
[release evidence](docs/V2_RELEASE_EVIDENCE.md).

## Readiness and limits

**Ready to use as a preparation and artifact-checking toolkit.** Before relying
on it during an event, verify loading in your chosen coding agent, complete one
end-to-end practice run and review the current edition's actual contract.
Toolkit validation and submission readiness are separate judgments.

- PASS means the configured check passed; it does not prove correct contract
  transcription or that every required check was configured.
- WARN needs review, FAIL needs correction and UNKNOWN means evidence is missing
  or unsupported. Workflow evaluation gates require PASS evidence. A passing
  `audit-selftest` tests the audits and cannot replace participant evaluation.
- Fixture commands need explicit `--allow-exec`. Executed code retains host
  permissions; this toolkit is not an OS sandbox. Nothing is submitted, deployed
  or uploaded automatically; no paid model call is made implicitly.
- Live agent activation, hidden-label accuracy and official scoring outcomes
  remain unverified. Check historical rubric weights and edition-specific log
  profiles against the actual event.

See [SECURITY.md](SECURITY.md) for trust boundaries and
[the field guide](docs/HACKATHON_GUIDE.md) for historical scoring and interview
preparation.

## Documentation and repository layout

| Location | What to read or use |
|---|---|
| `hackerrank-orchestrate/` | Core skill, references, ten checkers and templates |
| `skills/` | Four companions and the contract-driven submission packager |
| `orchestrate_toolkit/` | CLI, adapters, installer, evaluation, audits and workflow |
| [CLI.md](docs/CLI.md) | Exact commands, configuration, exit codes and recovery |
| [INSTALL.md](docs/INSTALL.md) / [COMPATIBILITY.md](docs/COMPATIBILITY.md) | Installation, activation procedures and evidence labels |
| [HACKATHON_GUIDE.md](docs/HACKATHON_GUIDE.md) | Preserved strategy, historical rubric, interviews and sources |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) / [COVERAGE.md](docs/COVERAGE.md) | Component boundaries and capability coverage |
| `integrations/` | Skill catalog, upstream revisions and compatibility metadata |
| `examples/offline/` | Executable synthetic walkthrough |
| `benchmarks/comparison/` | Identical-input fixtures, runner and measured reports |
| `tests/`, `evals/`, `tools/` | Regressions, trigger proxy, validators and packaging utilities |
| [CHANGELOG.md](CHANGELOG.md) / [CONTRIBUTING.md](CONTRIBUTING.md) | Release history and contribution checks |

## Development

```text
python tools/validate_skill.py
python tools/static_check.py
python -m orchestrate_toolkit audit-selftest
python -W error -m unittest discover -s tests -v
python tools/run_trigger_evals.py --offline --min-precision 0.6 --min-recall 0.5
python tools/ci_check.py
python tools/wheel_smoke.py
```

The wheel check needs locally installed pip, setuptools and wheel; its build and
temporary install use `--no-index`. Paid/live trigger evaluations are opt-in and
never run in CI. For their flags, use `tools/run_trigger_evals.py --help`.
See [CONTRIBUTING.md](CONTRIBUTING.md) before changing canonical skills or adapters.

## License and credits

[MIT license](LICENSE). The playbook independently restates ideas credited to
[Orchestrate-loop](https://github.com/bsrikumar855-dot/Orchestrate-loop); its
unlicensed prose is not copied. The optional
[community toolkit](https://github.com/NITISH-R-G/hackerrank-orchestrate-skills)
remains a separate project. Attribution and the upstream MIT notice are in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). No upstream implementation is
vendored. Historical organizer material and sources remain in the
[field guide](docs/HACKATHON_GUIDE.md#sources).
