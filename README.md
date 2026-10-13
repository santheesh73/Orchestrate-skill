# hackerrank-orchestrate

A Claude skill for competing in **HackerRank Orchestrate**, the 24-hour AI-agent hackathon graded on four artifacts: code zip, output CSV, AI judge interview and chat transcript.

It turns Claude into an event strategist that writes paste-ready prompts for Claude Code, checks the reports that come back against real artifacts, and keeps the build aligned with how the event is actually scored.

## What's inside

```
hackerrank-orchestrate/
├── SKILL.md                      router, working style, the one canonical copy of the hard rules
├── references/
│   ├── rubric.md                 weights, per-artifact sub-criteria, caps, tie-breaks, leaderboard calibration
│   ├── starter-contract.md       first-15-minutes checklist for a new starter repo (log tool= rule, usage report)
│   ├── archetypes/               one page per problem shape seen so far, plus an index
│   ├── loop-patterns.md          agent loop, Plan→Build→Review, change-record loop, relay, per-row safety, phase gates
│   ├── evaluation.md             generalization policy, anti-overfitting protocol, resolution table, noise floor
│   ├── output-csv.md             boundary calls, justification template, safety rows
│   ├── interview.md              question bank from your own code, answer shape, ownership, hour-before checklist
│   ├── self-score.md             gate 7 with or without the community toolkit
│   ├── winning-approaches.md     cross-cutting patterns from public top finishers
│   ├── prompt-templates.md       kickoff, iteration, targeted audit, output-row pass, final freeze
│   └── kit-repo.md               optional community toolkit digest
├── scripts/                      stdlib-only checkers (Python 3.9+)
│   ├── check_log.py              log.txt entries: tool= rule, prompt block, secrets, append-only
│   ├── preflight.py              output.csv: header, ids, enums, blanks
│   ├── rerun_diff.py             churn between two runs; noise floor
│   ├── usage_report.py           evaluation/usage_report.md from a per-call token log
│   └── interview_drill.py        interview questions from your constants, thresholds and orderings
└── assets/                       change record, decision log, CONSTANTS.md, usage-log schema
```

Outside the skill: `evals/triggers.json` (should and should-not trigger prompts), `tests/` (script tests on fixtures), `tools/validate_skill.py` (structure check run in CI).

## Install

**Claude Code:** copy the folder into your project or personal skills directory.

```bash
mkdir -p .claude/skills
cp -r hackerrank-orchestrate .claude/skills/
```

It triggers from its description; no slash command needed.

**Claude.ai:** zip the `hackerrank-orchestrate` folder (with `SKILL.md` at its top level) and upload it as a custom skill.

## Example prompts

```
Orchestrate starter repo just dropped. AGENTS.md and problem_statement.md are below. Give me the Claude Code kickoff prompt.
```

```
Here is the Claude Code report from the last round. Verify it and give me the next iteration prompt.
```

```
Interview opens in two hours. Build my drill from code/ and quiz me.
```

## Using the scripts

They check your work; keep them out of your submission (the participant must be its author). Each takes paths and schemas as arguments and embeds no dataset.

```bash
python hackerrank-orchestrate/scripts/check_log.py log.txt --expect-tool "Claude Code"
python hackerrank-orchestrate/scripts/preflight.py output.csv --template dataset/output.csv \
    --inputs dataset/requests.csv --id-col request_id --enum "status=a|b|c"
python hackerrank-orchestrate/scripts/rerun_diff.py run1.csv run2.csv --id-col request_id
python hackerrank-orchestrate/scripts/usage_report.py usage.jsonl --run-id final \
    --price "<model>=<in $/MTok>:<out $/MTok>" --out code/evaluation/usage_report.md
python hackerrank-orchestrate/scripts/interview_drill.py code/ --constants CONSTANTS.md
```

## Development

```bash
python tools/validate_skill.py
python -m unittest discover -s tests -v
```

## Status and caveats

- Scoring sub-criteria come from the organizer's post-mortem of the May 2026 edition and may change. The live challenge page wins on any conflict.
- Problem archetypes and patterns rest on the public material that was reachable (sources are linked in `rubric.md` and `winning-approaches.md`). They are patterns top finishers used, not proof of cause.
- Trigger accuracy is covered by `evals/triggers.json` but has not been measured against a live model run yet.
- Not affiliated with or endorsed by HackerRank.

## License

MIT. See [LICENSE](LICENSE).
