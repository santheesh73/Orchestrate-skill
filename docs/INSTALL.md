# Installing the skill in each coding agent

For V4, the standard-library CLI adds owned upgrade restoration and optional
edition workflow policies. See [V4 usage](V4_USAGE.md) and
[troubleshooting](TROUBLESHOOTING.md). Existing installation routes and agent IDs
are retained; a source upgrade is not a live-activation verification.

`hackerrank-orchestrate/` is one canonical folder with `SKILL.md`, references,
scripts and assets. Native skill loaders can read that format; instruction-file
adapters point to installed canonical guidance. These are different mechanisms.
The skill's content is agent-neutral and preserves the user's requested role.

## Universal CLI

Use `python -m orchestrate_toolkit install --agent NAME --project PATH --dry-run`
to preview, then omit --dry-run to install. This ownership-aware path also offers
doctor, backed-up owned upgrades and uninstall. See [CLI.md](CLI.md) and
[COMPATIBILITY.md](COMPATIBILITY.md) for all adapters and evidence. Original
packaging/install commands below remain supported; files installed by those
older tools are unowned conflicts for the new installer, never silently adopted.

Evidence labels used here:

- **VERIFIED**: the skill was installed and run in that agent, and it loaded.
- **DOCS-READ**: the agent's own documentation says so (URL and the date it was read). Nobody ran the skill there.
- **UNKNOWN**: neither.

## Where each agent looks

The table below records the earlier installation research and historical smoke
test. It does not establish current live inference. The universal CLI uses each
documented mechanism rather than assuming every agent loads `.agents/skills`.
Antigravity and Claude.ai retain their legacy documented/manual installation;
no new live verification or dedicated universal adapter is claimed for them.

| Agent | Project folder | Global folder | Evidence | Source, date read | Known caveat |
|---|---|---|---|---|---|
| Claude Code | `.claude/skills/` | `~/.claude/skills/` | VERIFIED (project folder, Claude Code 2.1.296, 2026-10-13; see Status) | [code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills), 2026-10-13 | All frontmatter fields are optional there; the description is truncated at 1,536 characters in the skill listing (ours is under 900). |
| Claude.ai | none (upload) | Settings > Capabilities > Skills > Upload skill, a zip of the folder | DOCS-READ | [support.claude.com, "Using skills in Claude"](https://support.claude.com/en/articles/12512180-using-skills-in-claude), 2026-10-13 | Needs code execution turned on; Pro, Max, Team and Enterprise plans. The upload fails if the folder name does not match `name`. |
| OpenAI Codex | `.agents/skills/` in every folder from the working directory up to the repository root | `~/.agents/skills/` (also `/etc/codex/skills` for a machine-wide copy) | DOCS-READ | [learn.chatgpt.com/docs/build-skills](https://learn.chatgpt.com/docs/build-skills) (redirected from developers.openai.com/codex/skills), 2026-10-13 | Requires `name` and `description`; no length limits are stated. |
| OpenCode | `.opencode/skills/`, `.claude/skills/` or `.agents/skills/` | `~/.config/opencode/skills/`, `~/.claude/skills/` or `~/.agents/skills/` | DOCS-READ | [opencode.ai/docs/skills](https://opencode.ai/docs/skills), 2026-10-13 | `name` must match the folder and `^[a-z0-9]+(-[a-z0-9]+)*$`, 1 to 64 characters; `description` 1 to 1024 characters. Installing with `--for all` puts two copies in its search path; they are identical. |
| Google Antigravity | `.agents/skills/` | `~/.gemini/config/skills/` | DOCS-READ | [Antigravity skills codelab](https://codelabs.developers.google.com/getting-started-with-antigravity-skills), 2026-10-13 | The same codelab gives `~/.gemini/antigravity-cli/skills/` for the Antigravity CLI and does not reconcile the two global paths. Only `description` is mandatory there. |
| Cursor | `.agents/skills/` or `.cursor/skills/` | `~/.agents/skills/` or `~/.cursor/skills/` | DOCS-READ | [cursor.com/docs/context/skills](https://cursor.com/docs/context/skills) and [forum thread 161142](https://forum.cursor.com/t/cursor-agent-skills-in-agents-skills/161142), 2026-10-13 | On 3.3.27 (May 2026) skills in `.agents/skills/` were listed but not injected into the agent's context. Cursor staff wrote on 2026-08-25 that "on current builds" it works and that stable is 3.17.8. Use a current build, and check that the agent actually reads the skill. |

### Status

Claude Code is the only one of these agents that was installed where this was written. On 2026-10-13 the skill was installed with `--for claude` into an empty project and run with Claude Code 2.1.296 in print mode. The skill was listed at start-up and invoked for an Orchestrate question ("starter repo just dropped, what do I check in the first 15 minutes"), and it was not invoked for a near miss ("write a prompt for Codex to refactor a React component"). That is one run of each, so it shows that the skill loads, not how accurately it triggers.

Claude.ai, Codex, OpenCode, Antigravity and Cursor were not run. Whether the skill loads and triggers there is UNKNOWN beyond what their docs say.

## Install

From a clone of this repository:

```bash
python3 -I tools/package_skill.py --project ../my-entry --for all      # both project folders
python3 -I tools/package_skill.py --project ../my-entry --for agents   # Codex, Cursor, OpenCode, Antigravity
python3 -I tools/package_skill.py --project ../my-entry --for claude   # Claude Code
python3 -I tools/package_skill.py --install ~/.agents/skills           # any one folder, for example a global one
python3 -I tools/package_skill.py                                       # dist/hackerrank-orchestrate.zip for Claude.ai
```

Each install copies a clean, validated folder (no caches, tests or fixtures) beside the target and swaps it in. An existing copy is replaced only with `--force`, and if anything fails the old copy stays as it was. With `--for all`, both targets are checked before either is written. On Windows, use `py -3 -I` in place of `python3 -I`.

Copying the folder by hand into one of the folders in the table also works.

## If the agent does not pick the skill up

Make the skill explicit in your first message instead:

```
Read <path>/hackerrank-orchestrate/SKILL.md and follow it for this event
```

`<path>` is the folder you installed into, for example `.agents/skills`. Do not add this to the starter's `AGENTS.md` or `CLAUDE.md`: those files are the event's logging contract, and hard rule 1 in `SKILL.md` keeps them as shipped.

## Running the bundled scripts from the installed folder

The scripts in `scripts/` use the standard library only (Python 3.9 or later) and make no network calls. Run them with `-I` so nothing from your project folder or user site-packages is imported in their place; add `-B` if you do not want `__pycache__` written into the skill folder.

POSIX (macOS, Linux):

```bash
python3 -I .agents/skills/hackerrank-orchestrate/scripts/check_log.py log.txt --expect-tool "HARNESS"
python3 -I .agents/skills/hackerrank-orchestrate/scripts/preflight.py --help
```

Windows (PowerShell or cmd):

```
py -3 -I .agents\skills\hackerrank-orchestrate\scripts\check_log.py log.txt --expect-tool "HARNESS"
py -3 -I .agents\skills\hackerrank-orchestrate\scripts\preflight.py --help
```

`HARNESS` is the exact name your agent writes on its `tool=` line; see `references/starter-contract.md` in the skill.

## Optional companion skills

The original install command above is unchanged. Validate or package the four
additions separately:

```text
python tools/package_addons.py --validate-only
python tools/package_addons.py --all --out dist/companions
python tools/package_addons.py --skill hackerrank-orchestrate-design --out dist/design
```

Add `--install <skill-directory>` to install the selected companions into the
same directory used by the original skill. For example:

```text
python tools/package_addons.py --all --out dist/companions --install ../my-entry/.agents/skills
python tools/package_addons.py --all --out dist/companions-claude --install ../my-entry/.claude/skills
```

Both archives and installed folders must be new. There is no overwrite flag;
every existing skill, including the original, is left intact. On Windows, use
`py -3` when needed. For Claude.ai, upload a companion's individual zip. Each
companion is self-contained and includes license/source notices. CLI package
installation is a separate optional operation documented in the toolkit
companion; installing skills does not install any external dependency.

Invoke the companion by its exact name if automatic selection is ambiguous.
Multi-skill routing in each harness has not been behaviorally measured.

Version 3.2 adds `hackerrank-orchestrate-evidence` as a fifth companion. The
universal installer discovers it with the existing companions, and the original
addon installer includes it under `--all`. For selective packaging, use
`--skill hackerrank-orchestrate-evidence`. Owned universal installations need an
explicit `--upgrade` when source files change; preview the upgrade first.
See [behavior evaluation](BEHAVIOR_EVALUATION.md) and
[live verification](LIVE_VERIFICATION.md). Installation is not live activation.
