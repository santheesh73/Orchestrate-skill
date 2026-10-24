# Agent compatibility and evidence

Sources were opened on 2026-10-24. The selected mechanism is documented;
filesystem/lifecycle tests simulate installation and do not run an agent model.
Every adapter is exercised by tests/test_universal.py. Final suite/CI evidence
is recorded in UNIVERSAL-RELEASE-REPORT.md.

| Agent | Installation mechanism | Discovery | Invocation | Tests | Status |
|---|---|---|---|---|---|
| OpenAI Codex | Native skill support | DOCS-READ; live UNKNOWN | $hackerrank-orchestrate | lifecycle simulation | [docs](https://learn.chatgpt.com/docs/build-skills); live UNKNOWN |
| Claude Code | Native skill support | DOCS-READ; live UNKNOWN | /hackerrank-orchestrate | lifecycle simulation | [docs](https://code.claude.com/docs/en/skills); live UNKNOWN |
| Cursor | Native instruction-file support | DOCS-READ; live UNKNOWN | @orchestrate | lifecycle simulation | [docs](https://cursor.com/docs/rules); live UNKNOWN |
| Windsurf | Native instruction-file support | DOCS-READ; live UNKNOWN | @orchestrate (legacy fallback path) | lifecycle simulation | [docs](https://docs.devin.ai/desktop/cascade/memories); live UNKNOWN |
| GitHub Copilot | Native instruction-file support | DOCS-READ; live UNKNOWN | Ask Copilot about an Orchestrate project file; surface-specific instructions must be enabled | lifecycle simulation | [docs](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions); live UNKNOWN |
| Gemini CLI | Native skill support | DOCS-READ; live UNKNOWN | /skills list; ask to activate hackerrank-orchestrate | lifecycle simulation | [docs](https://geminicli.com/docs/cli/skills/); live UNKNOWN |
| Cline | Native instruction-file support | DOCS-READ; live UNKNOWN | Enable the Orchestrate workspace rule and request the skill | lifecycle simulation | [docs](https://docs.cline.bot/customization/cline-rules); live UNKNOWN |
| Roo Code | Native instruction-file support | DOCS-READ; live UNKNOWN | Request the Orchestrate workflow | lifecycle simulation | [docs](https://roocodeinc.github.io/Roo-Code/features/custom-instructions/); live UNKNOWN |
| Continue | Native instruction-file support | DOCS-READ; live UNKNOWN | Select the Orchestrate rule in the rules UI | lifecycle simulation | [docs](https://docs.continue.dev/customize/deep-dives/rules); live UNKNOWN |
| Aider | CLI-assisted support | DOCS-READ; live UNKNOWN | aider --read .orchestrate/adapters/aider.md | lifecycle simulation | [docs](https://aider.chat/docs/usage/conventions.html); live UNKNOWN |
| OpenCode | Native skill support | DOCS-READ; live UNKNOWN | Ask to load hackerrank-orchestrate using the skill tool | lifecycle simulation | [docs](https://opencode.ai/docs/skills/); live UNKNOWN |
| Other instruction-capable agents | Manual compatibility | manual fallback; live UNKNOWN | Read .orchestrate/adapters/portable.md explicitly | lifecycle simulation | manual; live UNKNOWN |

## Installed paths and activation

- **OpenAI Codex**: `.agents/skills`. $hackerrank-orchestrate. User-global native skill path supported.
- **Claude Code**: `.claude/skills`. /hackerrank-orchestrate. User-global native skill path supported.
- **Cursor**: `.cursor/rules/orchestrate.mdc`. @orchestrate. Project-local or manual only; no global path invented.
- **Windsurf**: `.windsurf/rules/orchestrate.md`. @orchestrate (legacy fallback path). Project-local or manual only; no global path invented.
- **GitHub Copilot**: `.github/instructions/orchestrate.instructions.md`. Ask Copilot about an Orchestrate project file; surface-specific instructions must be enabled. Project-local or manual only; no global path invented.
- **Gemini CLI**: `.gemini/skills`. /skills list; ask to activate hackerrank-orchestrate. User-global native skill path supported.
- **Cline**: `.clinerules/orchestrate.md`. Enable the Orchestrate workspace rule and request the skill. Project-local or manual only; no global path invented.
- **Roo Code**: `.roo/rules/orchestrate.md`. Request the Orchestrate workflow. Project-local or manual only; no global path invented.
- **Continue**: `.continue/rules/orchestrate.md`. Select the Orchestrate rule in the rules UI. Project-local or manual only; no global path invented.
- **Aider**: `.orchestrate/adapters/aider.md`. aider --read .orchestrate/adapters/aider.md. Project-local or manual only; no global path invented.
- **OpenCode**: `.agents/skills`. Ask to load hackerrank-orchestrate using the skill tool. User-global native skill path supported.
- **Other instruction-capable agents**: `.orchestrate/adapters/portable.md`. Read .orchestrate/adapters/portable.md explicitly. Project-local or manual only; no global path invented.

## Verification procedure and limits

After installation, open the agent in the target project and ask it to identify
the exact skill path and the first contract check. Confirm the path in tool
evidence, then try an unrelated request to check accidental activation. Record
the version, configuration and actual invocation. No such new live run has been
performed here; a detected executable does not establish support.

Windsurf documentation now redirects to Devin Desktop; the adapter uses the
documented legacy .windsurf/rules fallback and manual trigger. Cursor uses an
instruction rule despite supporting other mechanisms in some builds. Copilot
features vary across IDE, review and cloud surfaces. Disabled rules, trust dialogs
and permissions can prevent loading.

The old Claude Code smoke run verified the original core once, not this universal
installer or any current runtime. Antigravity and Claude.ai retain legacy
documented/manual paths in INSTALL.md; use portable instructions for other
unregistered agents. Unknown agent IDs and undocumented global rule formats are
unsupported by this CLI. No agent is launched or paid API used by compatibility.
