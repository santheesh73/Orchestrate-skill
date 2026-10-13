# HackerRank Orchestrate: how to approach it, and a Claude skill to help

[![validate](https://github.com/santheesh73/Orchestrate-skill/actions/workflows/validate.yml/badge.svg)](https://github.com/santheesh73/Orchestrate-skill/actions/workflows/validate.yml)

This repository has two parts:

1. **A field guide to HackerRank Orchestrate** (this README): what the event is, how it is scored, and a tested way to approach the 24 hours.
2. **`hackerrank-orchestrate/`**, a Claude skill that applies this guide during the event. It writes your Claude Code prompts, checks the reports that come back, and includes scripts that catch the mistakes that cost the most points.

> **The live challenge page and your edition's `AGENTS.md` and `problem_statement.md` always win.** The format changes between editions. Everything here comes from public material on past editions, linked in [Sources](#sources).

---

## Contents

- [What Orchestrate is](#what-orchestrate-is)
- [How it is scored](#how-it-is-scored)
- [What separates the top 50](#what-separates-the-top-50)
- [How to approach it](#how-to-approach-it)
  - [Before the event](#before-the-event)
  - [The first 15 minutes: read the contract](#the-first-15-minutes-read-the-contract)
  - [Hours 0 to 3: plan and architecture](#hours-0-to-3-plan-and-architecture)
  - [Hours 3 to 13: build and iterate with evidence](#hours-3-to-13-build-and-iterate-with-evidence)
  - [Hours 13 to 18: output rows and self-score](#hours-13-to-18-output-rows-and-self-score)
  - [Hours 18 to 24: interview prep, freeze, submit](#hours-18-to-24-interview-prep-freeze-submit)
  - [The interview](#the-interview)
- [Rules that hold up across editions](#rules-that-hold-up-across-editions)
- [Common mistakes](#common-mistakes)
- [Using the skill](#using-the-skill)
- [Repository layout](#repository-layout)
- [Sources](#sources)
- [Caveats and license](#caveats-and-license)
- [Credits](#credits)

---

## What Orchestrate is

HackerRank Orchestrate is a recurring, global, solo hackathon for building an **AI agent** in a tight window, usually 24 hours. Each edition releases a fresh problem and an official starter repository containing:

- `problem_statement.md`: the task, input files, output schema, allowed values and evaluation notes
- `AGENTS.md`: rules for any AI coding tool working in the repo, including **mandatory session logging** to `log.txt`
- `CLAUDE.md`: a single line, `@AGENTS.md`, so Claude Code loads those rules automatically
- `dataset/`: inputs, a small set of solved sample rows, and a blank output template
- `code/`: an entry point to build from

You build the agent, run it over every input row, and submit three things: a **code zip**, the generated **output CSV**, and your **AI chat transcript**. After submitting you take a **live interview with an AI judge** about your solution.

Problems so far have taken different shapes: support-ticket triage over a document corpus (May 2026), claim verification against images (June 2026), adversarial message routing (August 2026), and a financial "buy or wait" planner over dated records (September 2026). Expect something new each time. The reliable skills are the approach, not the domain.

## How it is scored

Four artifacts, 100 points:

| Artifact | Points | What is judged |
|---|---|---|
| **Code zip** | 30 | Agent architecture 30% · prompt and tool craft 30% · robustness 25% · engineering rigor 15% |
| **Output CSV** | 30 | Per-row accuracy against a hidden golden set, plus a separate adversarial safety score |
| **AI judge interview** | 30 | Technical depth and ownership 40% · problem understanding and judgment 25% · communication 20% · honesty 15% |
| **Chat transcript** | 10 | Direction and architecture ownership 35% · technical specificity 25% · iteration and verification 25% · safety and edge cases 15% |

Sub-weights are from the organizer's post-mortem of the May 2026 edition. Rules worth knowing:

- **The code grader reads source only.** README claims earn nothing in the code score; design reasons belong in code comments and docstrings.
- **A generic justification caps a row at about 70%,** even when the label is right.
- **Escalating or refusing everything is invalid.**
- **Short interview answers score low.** The organizer measured a correlation of about −0.57.
- **Ties break on interview, then code, then output, then transcript.**
- Since September 2026, `code.zip` must include **`evaluation/usage_report.md`** (model calls, tokens and estimated cost for the final run), and every log entry needs a valid **`tool=` line** naming your coding harness.

## What separates the top 50

From public leaderboards for the May, June and August 2026 editions:

- **Balance beats a peak.** Most of each top 50 was in the top quartile on **all four** artifacts. Every top-10 finisher was, per the organizer.
- **The output CSV is where strong teams lose.** It was the weakest stage for 49 of the June top 50 and 34 of the August top 50. Great code with a mediocre CSV is the typical top-50 profile, so getting the rows right is how you separate.
- **The transcript and interview are cheap points most people leave behind.** Field medians are around 1.4 to 3.8 out of 10 for transcript and 11 to 15 out of 30 for interview. Top-50 averages are 63% to 89% of the maximum.
- **Simple, explainable architectures win.** A single agent with tools held 7 of the May top 10. One June author's earlier 15-stage pipeline finished mid-pack because they couldn't measure what each stage contributed. Their next, smaller design did far better.
- **Behavior beats tooling.** Claude Code users were overrepresented at the top, but the organizer credits *how* people worked: reasoning about tradeoffs, evidence, and visible ownership of decisions.

## How to approach it

The core idea: **the model describes, code decides.** The model reads messages, documents and images and returns a typed record of what it observed. Plain, unit-tested code turns that record into every number, label and plan. That makes the run repeatable from a cache, auditable row by row, and resistant to prompt injection by structure. It also gives you strong answers for the interview.

### Before the event

- Clone a past starter repo (for example [september26](https://github.com/interviewstreet/hackerrank-orchestrate-september26)) and do a **compressed mock run** of a few hours. The point is to rehearse the loop, not to win the old problem.
- Set up your tools: Claude Code (or your harness of choice), an API key in an environment variable, and this skill.
- Know the deadline in your own timezone, and when the interview window opens.
- Plan to sleep. Rehearsing the interview while exhausted is a known failure.

### The first 15 minutes: read the contract

Contract misses cost points that no model quality can recover. Before any design:

1. Read `AGENTS.md`, `problem_statement.md` and `README.md` **in full**, not from memory of a past edition.
2. **Don't overwrite `CLAUDE.md`.** Its `@AGENTS.md` import is what makes the mandatory logging run, and your transcript is graded from that log. Add strategy below the import, or send it as your first message.
3. Write down every MUST: output file and location, exact columns and order, allowed values and formats, one row per input id, required extra files (such as `usage_report.md`), the log format and `tool=` rule, forbidden inputs (organizer-only files, hardcoded labels), and any stated conflict-resolution or tie-break order.
4. Compare with the last edition you know. New sections are where the new traps are.
5. Put that MUST list into your first prompt so the build starts against it.

### Hours 0 to 3: plan and architecture

- **Plan out loud before any code.** State the approach, the alternatives, and why you picked one. Transcript ownership is 35% of that score and can't be added after the fact.
- **Identify the problem's shape** (retrieval, multimodal verification, adversarial routing, simulation and planning, or something new) and start from what worked for that shape.
- **Design one findable agent loop:** a named function or graph with an explicit step cap, a fallback, and a validated final-answer schema. A framework or the raw API both work. A hidden decision tree passed off as a "loop" does not.
- **Draw the seam.** Decide what the model observes, what code decides, and which inputs are attacker-controlled. Fence untrusted content.
- **Decide grouping keys and statistics before writing detectors.** Patches inherit whatever the grouping already threw away.
- **Cache every model record** by content hash and prompt version, so you can iterate on rules offline for free.
- **Log every model call** (provider, model, tokens, row id) from the first paid call. You need this for the usage report.

### Hours 3 to 13: build and iterate with evidence

Every non-trivial change gets a short record:

```
CHANGE / REQUIREMENT / CEILING / CLAIM / JUSTIFICATION / METRIC /
BASELINE / RESULT / BLAST RADIUS / COUNTERFACTUAL / VERDICT
```

- **Compute the ceiling first.** If a gap touches two rows, it isn't worth an hour.
- **Justify with the domain, not the samples.** Sample rows can show that a case exists or that a rule is wrong. They are never a rule's only reason. Never tune until one sample number matches.
- **One labeled row is noise.** With 20 to 30 samples, one row is 3 to 5 points. Revert when a label-free check regresses, or when two or more labeled rows regress for reasons you can't explain.
- **Diff the whole output** after every core change, not just the field you targeted. Measure the model's run-to-run noise once, so you know what size of change actually means something.
- **Prove counterfactuals.** Turn a component off and show its effect stops.
- **One bad row never kills the run.** Validate, retry once, then write an honest escalation or safe-default row. Never write a partial output file.
- **Keep `CONSTANTS.md`** with a provenance column for every tunable number (measured, spec, standard, bound or judgement), and put the same reason in a comment beside the constant.

### Hours 13 to 18: output rows and self-score

- **Attack the boundary calls.** Top finishers mostly lose rows where the model's default guess sits near the line between two classes. Write resolved definitions with contrastive examples into the prompt, rather than tuning thresholds against a handful of samples.
- **Make justifications specific:** the decision, the rule that fired, the evidence ids actually read, and the alternative that lost. If a justification would read the same on another row, it's generic.
- **Check the adversarial rows separately,** since they carry their own safety score. Check that the output hasn't collapsed onto one value.
- **Self-score every artifact honestly** against the rubric. Name the weakest one and spend the next block there.

### Hours 18 to 24: interview prep, freeze, submit

- **Freeze the code early enough** to run from a fresh clone using only your README, rerun the full dataset once, and generate the usage report from that exact run.
- **Re-derive every number** you cite (test counts especially) from the live repo. Docs drift under heavy iteration.
- **Confirm the code zip, output CSV and log tell the same story.** No secrets, no organizer-only files, `CLAUDE.md` untouched.
- **Rehearse the interview** before you're under deadline pressure.

### The interview

The judge asks about **your** code, not about agents in general. In one first-hand September 2026 account, the questions were things like "which statistic estimates variable spend?" and "on the same date, which is applied first, the debit or the credit?". A candidate answered "debits first" while their code applied credits first, and lost points for contradicting the implementation.

- **Build your question bank from your code:** every constant, threshold, sort order and gate, each answered against the line it lives on.
- **Answer in this shape:** decision, the alternative you rejected, the evidence, the limitation. Four sentences or more, never one line.
- **Own it precisely:** "I chose X because…", and be clear about which parts you designed and which an AI tool generated.
- **Have these ready:** one row traced end to end, three rejected changes with the numbers that killed them, where your determinism guarantee stops, and two limitations to volunteer before you're asked.
- **Never claim** "fully deterministic", "100%" without the set and its size, "no dataset-specific assumptions" without a test proving it, or "I wrote every line myself".

## Rules that hold up across editions

1. Don't overwrite `CLAUDE.md`. Obey the starter contract literally.
2. Samples motivate or falsify; the domain justifies.
3. One labeled row is noise.
4. Decide grouping keys and statistics before writing detectors.
5. Never gate a decision on the truthiness of a model-written free-text field. Use booleans and enums.
6. Every non-trivial change gets a change record.
7. Rationale lives in source, not the README.
8. Every constant has a provenance.
9. Prove counterfactuals.
10. One bad row never kills the run.
11. Self-score is never skipped.
12. Rehearse the interview early, from your own code.
13. State the boundary of every guarantee, and name your limitations first.

## Common mistakes

| Mistake | Instead |
|---|---|
| Accepting the first architecture the AI proposes | Compare alternatives out loud and choose yourself |
| One giant prompt that does everything | Narrow model jobs over a tested deterministic core |
| Letting the agent run unsupervised for hours | Short cycles: plan, build, review, with a change record |
| Testing only the happy path | Adversarial and malformed inputs before writing input handling |
| Leaving evaluation and the CSV to the last hour | Reserve hours 13 to 18 for rows and self-scoring |
| Explaining the design only in the README | Docstrings and comments beside the code they govern |
| Tuning thresholds until the samples match | Domain-justified rules, checked against samples |
| A `tool=` line holding a model name, or missing | The harness name in every log entry, checked before submitting |
| Reconstructing token usage after the fact | Log every call from the start |
| Rehearsing the interview at 3 AM | Rehearse once the code is frozen, then sleep |

---

## Using the skill

`hackerrank-orchestrate/` is a Claude skill that applies everything above during the event. By default it acts as your strategist: it writes paste-ready prompts for Claude Code, checks the report that comes back against real artifacts, and writes the next prompt. It never invents a schema, score or test count.

### Install

**Claude Code:** copy the folder into your project or your personal skills directory. It triggers from its description; no slash command is needed.

```bash
mkdir -p .claude/skills
cp -r hackerrank-orchestrate .claude/skills/
```

**Claude.ai:** zip the `hackerrank-orchestrate` folder (with `SKILL.md` at its top level) and upload it as a custom skill.

### Example prompts

```
The Orchestrate starter repo just dropped. AGENTS.md and problem_statement.md are below. Give me the Claude Code kickoff prompt.
```

```
Here is the Claude Code report from the last round. Verify it and give me the next iteration prompt.
```

```
The output CSV is my weakest stage. Give me an output-row pass prompt.
```

```
The interview opens in two hours. Build my drill from code/ and quiz me.
```

### Checker scripts

Standard-library Python 3.9+, nothing to install. Each takes paths and schemas as arguments and embeds no dataset.

| Script | What it catches |
|---|---|
| `check_log.py log.txt --expect-tool "Claude Code"` | Missing, placeholder, generic or model-name `tool=` lines; empty prompt blocks; secrets; non-append-only timestamps |
| `preflight.py output.csv --template dataset/output.csv --inputs dataset/<inputs>.csv --id-col <id> --enum "col=a\|b"` | Wrong header or column order, missing or duplicate ids, off-enum values, blanks, a collapsed distribution |
| `rerun_diff.py run1.csv run2.csv --id-col <id>` | Row and column churn between runs; your noise floor |
| `usage_report.py usage.jsonl --run-id final --price "<model>=<in>:<out>"` | Builds `evaluation/usage_report.md` with per-model and overall totals |
| `interview_drill.py code/ --constants CONSTANTS.md` | Interview questions from your constants, thresholds, orderings and statistics, each with `file:line`, plus constants missing from `CONSTANTS.md` |

All scripts live in `hackerrank-orchestrate/scripts/`. **They check your work and are not part of your submission.** The rules require the participant to be the author.

## Repository layout

```
hackerrank-orchestrate/           the skill
├── SKILL.md                      router, working style, the canonical hard rules
├── references/
│   ├── rubric.md                 scoring, caps, tie-breaks, leaderboard calibration
│   ├── starter-contract.md       first-15-minutes checklist, tool= rule, usage report
│   ├── archetypes/               one page per problem shape seen so far
│   ├── loop-patterns.md          agent loop, change-record loop, relay, per-row safety, phase gates
│   ├── evaluation.md             generalization policy, anti-overfitting, resolution table, noise floor
│   ├── output-csv.md             boundary calls, justifications, safety rows
│   ├── interview.md              question bank, answer shape, ownership, hour-before checklist
│   ├── self-score.md             gate 7, with or without the community toolkit
│   ├── winning-approaches.md     cross-cutting patterns from top finishers
│   ├── prompt-templates.md       kickoff, iteration, audit, output-row pass, freeze
│   └── kit-repo.md               optional community toolkit digest
├── scripts/                      the five checkers above
└── assets/                       change record, decision log, CONSTANTS.md, usage-log schema
evals/triggers.json               prompts that should and should not trigger the skill
tests/                            script tests on small fixtures
tools/validate_skill.py           structure check, run in CI
```

Development:

```bash
python tools/validate_skill.py
python -m unittest discover -s tests -v
```

## Sources

- [HackerRank: Behind the Scenes of Orchestrate](https://www.hackerrank.com/blog/behind-the-scenes-of-hackerrank-orchestrate/): organizer post-mortem with sub-rubrics, caps, tie-breaks and what top finishers did
- [May 2026 #1 repository](https://github.com/saai-syvendra/hackerrank-orchestrate) and [write-up](https://saai.syvendra.com/myspace/hackerrank-orchestrate)
- Official starter repos: [june26](https://github.com/interviewstreet/hackerrank-orchestrate-june26), [september26](https://github.com/interviewstreet/hackerrank-orchestrate-september26)
- [A first-hand September 2026 AI-judge interview](https://dev.to/earlgreyhot1701d/my-first-ai-judge-interview-what-could-possibly-go-wrong-22el)
- [A practitioner's guide across three editions](https://medium.com/@shreesh.exe22/hackerrank-orchestrate-3268f0d710a5)
- Public leaderboards for the May, June and August 2026 editions (percentages computed from that data)
- [October 2026 challenge page](https://www.hackerrank.com/hackerrank-orchestrate-october26)

## Caveats and license

- Scoring sub-weights come from the May 2026 post-mortem, and later editions may reweight. Check the live page.
- Patterns come from the few public top-finisher repos and write-ups that were reachable. They describe what top finishers did, not proof of what caused their rank.
- **Trigger accuracy against a live model: UNKNOWN.** `tools/run_trigger_evals.py --live` exists but has not been run, because no API key was available where this was built. What *was* measured is an offline lexical-overlap proxy over the 44 cases in `evals/triggers.json` (22 should trigger, 22 should not): precision 0.72, recall 0.59 at threshold 0.3 (MEASURED, proxy only; it is not model behavior).
- Not affiliated with or endorsed by HackerRank.

MIT licensed. See [LICENSE](LICENSE).

## Credits

- Ideas, structure and the first set of lessons came from [orchestrate-loop](https://github.com/bsrikumar855-dot/orchestrate-loop), an earlier Orchestrate skill. That repository has no license, so none of its text is copied here; this repository is an independent rewrite that credits it as a source of ideas.
- The optional toolkit digest summarizes the community `hackerrank-orchestrate-skills` toolkit, as described secondhand in orchestrate-loop. Credit for that method belongs to its authors.
- Neither project is affiliated with this one, and none of them is affiliated with or endorsed by HackerRank.
