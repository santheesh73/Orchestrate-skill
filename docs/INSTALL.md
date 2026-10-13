# Installing the skill in each coding agent

`hackerrank-orchestrate/` is one folder with a `SKILL.md` at its top (frontmatter `name` and `description` only) plus `references/`, `scripts/` and `assets/`. Every agent below reads that same folder unchanged; only the place you put it differs. The skill's content is agent-neutral: it drafts prompts for whichever coding agent you drive.

Evidence labels used here:

- **VERIFIED**: the skill was installed and run in that agent, and it loaded.
- **DOCS-READ**: the agent's own documentation says so (URL and the date it was read). Nobody ran the skill there.
- **UNKNOWN**: neither.

## Where each agent looks

`.agents/skills/` is the common project folder: Codex, Cursor, OpenCode and Antigravity all read it. Claude Code reads `.claude/skills/`, and Claude.ai takes a zip upload.

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
