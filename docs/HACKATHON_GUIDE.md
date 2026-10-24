# Orchestrate hackathon field guide

This preserves the original planning, scoring, iteration and interview guidance.
The public sources were originally reviewed on 2026-10-13; these are historical
observations, not a specification for a new edition. Follow the actual starter
instructions and current challenge page. For current skills, installation,
commands and verification limits, start with the [repository README](../README.md).
Run repository-relative commands from the repository root.

## What Orchestrate is

HackerRank Orchestrate is a recurring, global, solo hackathon for building an **AI agent** in a tight window, usually 24 hours. Each edition releases a fresh problem and an official starter repository containing:

- `problem_statement.md`: the task, input files, output schema, allowed values and evaluation notes
- `AGENTS.md`: rules for any AI coding tool working in the repo, including **mandatory session logging** to `log.txt`
- `CLAUDE.md`: a single line, `@AGENTS.md`, so Claude Code loads those rules automatically
- `dataset/`: inputs, a small set of solved sample rows, and a blank output template
- `code/`: an entry point to build from

You build the agent, run it over every input row, and submit three things: a **code zip**, the generated **output CSV**, and your **AI chat transcript**. After submitting you take a **live interview with an AI judge** about your solution.

Problems so far have taken different shapes: support-ticket triage over a document corpus (May 2026), claim verification against images (June 2026), adversarial message routing (August 2026, as described in orchestrate-loop), and a financial "buy or wait" planner over dated records (September 2026). Expect something new each time. The reliable skills are the approach, not the domain.

## How it is scored

Four artifacts, 100 points:

| Artifact | Points | What is judged |
|---|---|---|
| **Code zip** | 30 | Agent architecture 30% · prompt and tool craft 30% · robustness 25% · engineering rigor 15% |
| **Output CSV** | 30 | Per-row correctness against a hidden golden set, plus one 0–100 safety score for the submission as a whole |
| **AI judge interview** | 30 | Technical depth and ownership 40% · problem understanding and judgment 25% · communication 20% · honesty 15% |
| **Chat transcript** | 10 | Direction and architecture ownership 35% · technical specificity 25% · iteration and verification 25% · safety and edge cases 15% |

Sub-weights are from the organizer's post-mortem of the May 2026 edition. Rules worth knowing:

- **The code grader reads source only.** README claims earn nothing in the code score; design reasons belong in code comments and docstrings.
- **A generic justification caps a row at about 70 out of 100,** even when the label is right.
- **Escalating everything is invalid, and so is replying to everything.**
- **Very short interview answers score low.** In the organizer's interview transcripts, its "very short answers" measure correlated with interview score at r = −0.568; total words spoken correlated positively (r = 0.615), and the number of turns only weakly negatively (no value published).
- **Ties break on interview, then code, then output, then transcript.**
- Since September 2026, `code.zip` must include **`evaluation/usage_report.md`** (model calls, tokens and estimated cost for the final run), and every log entry needs a valid **`tool=` line** naming your coding harness.

## What separates the top 50

Labels: **VERIFIED** means read in the organizer's post-mortem; **INFERRED** means computed by [orchestrate-loop](https://github.com/bsrikumar855-dot/orchestrate-loop) from public leaderboard data that could not be re-checked here. The full table is in [`rubric.md`](../hackerrank-orchestrate/references/rubric.md#5-what-the-leaderboards-show).

- **Balance beats a peak.** Every top-10 finisher in May was in the top quartile on all four artifacts, and so were 37 of the May top 50, with 11 more on three of the four (VERIFIED). Most of the June and August top 50 were too (INFERRED).
- **The output CSV is where strong teams lose.** It was the weakest stage for 49 of the June top 50 and 34 of the August top 50 (INFERRED). Great code with a mediocre CSV is the typical top-50 profile, so getting the rows right is how you separate.
- **The transcript and interview are cheap points most people leave behind.** Across the field, the median transcript score sat roughly between 1.4 and 3.8 of 10, and the median interview score between 11 and 15 of 30, while top-50 averages were 63% to 89% of the maximum (INFERRED).
- **Simple, explainable architectures win.** A single agent with tools held 7 of the May top 10 (VERIFIED). One June author had earlier entered with a 15-stage pipeline and placed mid-table, unable to show what any one stage added; their next, smaller design did far better (INFERRED, from that author's write-up as summarized in orchestrate-loop).
- **Behavior beats tooling.** Claude Code was used by 44% of the May top 50 versus 14.4% of all transcripts, but the organizer credits *how* people worked: reasoning about tradeoffs, evidence, and visible ownership of decisions (VERIFIED).

## How to approach it

The core idea: **the model describes, code decides** (the skill's core principle in [`SKILL.md`](../hackerrank-orchestrate/SKILL.md), detailed in [`winning-approaches.md`](../hackerrank-orchestrate/references/winning-approaches.md) §1). The model only reports what it observed; tested code produces every final value. You get a run you can repeat from a cache, audit row by row, and defend against injected text, plus strong interview answers.

### Before the event

- Clone a past starter repo (for example [september26](https://github.com/interviewstreet/hackerrank-orchestrate-september26)) and do a **compressed mock run** of a few hours. The point is to rehearse the loop, not to win the old problem.
- Set up your tools: Claude Code (or your harness of choice), an API key in an environment variable, and this skill.
- Know the deadline in your own timezone, and when the interview window opens.
- Plan to sleep. Rehearsing the interview while exhausted is a known failure.

### The first 15 minutes: read the contract

Contract misses cost points that no model quality can recover. Before any design:

1. Read `AGENTS.md`, `problem_statement.md` and `README.md` **in full**, not from memory of a past edition.
2. **Don't edit `AGENTS.md` or overwrite `CLAUDE.md`.** `AGENTS.md` is what makes the mandatory logging run (`CLAUDE.md` just imports it with `@AGENTS.md`), and your transcript is graded from that log. Send strategy as your first message, or add it below the import.
3. Write down every MUST: output file and location, exact columns and order, allowed values and formats, one row per input id, required extra files (such as `usage_report.md`), the log format and `tool=` rule, forbidden inputs (organizer-only files, hardcoded labels), and any stated conflict-resolution or tie-break order.
4. Compare with the last edition you know. New sections are where the new traps are.
5. Put that MUST list into your first prompt so the build starts against it.

### Hours 0 to 3: plan and architecture

- **Plan out loud before any code.** State the approach, the alternatives, and why you picked one. Transcript ownership is 35% of that score and can't be added after the fact.
- **Identify the problem's shape** (retrieval, multimodal verification, adversarial routing, simulation and planning, or something new) and start from what worked for that shape.
- **Design one findable agent loop:** a named function or graph with an explicit step cap, a fallback, and a validated final-answer schema. A framework or the raw API both work. A hidden decision tree passed off as a "loop" does not.
- **Draw the seam.** Decide what the model observes, what code decides, and which inputs are attacker-controlled. Fence untrusted content.
- **Choose how rows are grouped before writing any detector** (hard rule 5).
- **Cache every model record** by content hash and prompt version, so you can iterate on rules offline for free.
- **Log every model call** (provider, model, tokens, row id) from the first paid call. You need this for the usage report.

### Hours 3 to 13: build and iterate with evidence

Every non-trivial change gets a short record:

```
CHANGE / REQUIREMENT / CEILING / CLAIM / JUSTIFICATION / METRIC /
BASELINE / RESULT / BLAST RADIUS / COUNTERFACTUAL / VERDICT
```

- **Compute the ceiling first.** If a gap touches two rows, it isn't worth an hour.
- **Diff the whole output** after every core change, not just the field you targeted. Measure the model's run-to-run noise once, so you know what size of change actually means something. With 20 to 30 labeled samples, one row is 3 to 5 points.
- **Iterate under the hard rules** on samples, noise, counterfactuals, row safety and constants: rules 3, 4, 9, 10 and 11 in [`SKILL.md`](../hackerrank-orchestrate/SKILL.md#hard-rules-canonical-copy-other-files-link-here). The decision table behind them is in [`evaluation.md`](../hackerrank-orchestrate/references/evaluation.md) §4.

### Hours 13 to 18: output rows and self-score

- **Attack the boundary calls.** Top finishers mostly lose rows where the model's default guess sits near the line between two classes. Write resolved definitions with contrastive examples into the prompt, rather than tuning thresholds against a handful of samples.
- **Make justifications specific:** the decision, the rule that fired, the evidence ids actually read, and the alternative that lost. If a justification would read the same on another row, it's generic.
- **Check the adversarial rows separately,** since safety is scored on its own. Check that the output hasn't collapsed onto one value.
- **Self-score every artifact honestly** against the rubric. Name the weakest one and spend the next block there.

### Hours 18 to 24: interview prep, freeze, submit

- **Freeze the code early enough** to run from a fresh clone using only your README, rerun the full dataset once, and generate the usage report from that exact run.
- **Re-derive every number** you cite (test counts especially) from the live repo. Docs drift under heavy iteration.
- **Confirm the code zip, output CSV and log tell the same story.** No secrets, no organizer-only files, `AGENTS.md` and `CLAUDE.md` untouched.
- **Rehearse the interview** before you're under deadline pressure.

### The interview

The judge asks about **your** code, not about agents in general. In one [first-hand September 2026 account](https://dev.to/earlgreyhot1701d/my-first-ai-judge-interview-what-could-possibly-go-wrong-22el), the questions included what value estimated variable expenses and what happened first when salary and bills landed on the same day. The author's own earlier report said debits came first, but the submitted code applied credits first. Their lesson: the real questions were more specific than anything they had prepared for.

- **Build your question bank from your code:** every constant, threshold, sort order and gate, each answered against the line it lives on.
- **Answer in this shape:** decision, the alternative you rejected, the evidence, the limitation. Four sentences or more, never one line.
- **Own it precisely:** "I chose X because…", and be clear about which parts you designed and which an AI tool generated.
- **Have these ready:** one row traced end to end, three rejected changes with the numbers that killed them, where your determinism guarantee stops, and two limitations to volunteer before you're asked.
- **Never claim** "fully deterministic", "100%" without the set and its size, "no dataset-specific assumptions" without a test proving it, or "I wrote every line myself".

## Rules that hold up across editions

The skill keeps one canonical list of 14 hard rules in [`SKILL.md`](../hackerrank-orchestrate/SKILL.md#hard-rules-canonical-copy-other-files-link-here), and the evaluation rules behind them in [`evaluation.md`](../hackerrank-orchestrate/references/evaluation.md). They are not repeated here so the two can't drift apart. The three that cost the most points when broken: don't edit the starter's `AGENTS.md` or `CLAUDE.md`; samples motivate or falsify, but only the domain justifies a rule; one labeled row is noise.

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

## Sources

- [HackerRank: Behind the Scenes of Orchestrate](https://www.hackerrank.com/blog/behind-the-scenes-of-hackerrank-orchestrate/): organizer post-mortem with sub-rubrics, caps, tie-breaks and what top finishers did
- [May 2026 #1 repository](https://github.com/saai-syvendra/hackerrank-orchestrate) and [write-up](https://saai.syvendra.com/myspace/hackerrank-orchestrate)
- Official starter repos: [june26](https://github.com/interviewstreet/hackerrank-orchestrate-june26), [september26](https://github.com/interviewstreet/hackerrank-orchestrate-september26)
- [A first-hand September 2026 AI-judge interview](https://dev.to/earlgreyhot1701d/my-first-ai-judge-interview-what-could-possibly-go-wrong-22el)
- [A practitioner's guide across three editions](https://medium.com/@shreesh.exe22/hackerrank-orchestrate-3268f0d710a5)
- Public leaderboards for the May, June and August 2026 editions (per-stage percentages computed secondhand from that data; INFERRED)
- [October 2026 challenge page](https://www.hackerrank.com/hackerrank-orchestrate-october26)

The links above were reviewed on 2026-10-13. The community
[hackerrank-orchestrate-skills toolkit](https://github.com/NITISH-R-G/hackerrank-orchestrate-skills)
was inspected directly on 2026-10-24 at the revision recorded in
[`integrations/upstreams.json`](../integrations/upstreams.json).

## Credits

- Ideas, structure and the first set of lessons came from [orchestrate-loop](https://github.com/bsrikumar855-dot/orchestrate-loop), an earlier Orchestrate skill. That repository has no license, so its prose is not copied here; this repository is an independent rewrite that credits it as a source of ideas. What it shares with orchestrate-loop is factual: the leaderboard figures in `references/rubric.md` (labeled INFERRED, with this credit), the toolkit's command lines, and file and rule names.
- The optional toolkit integration now references its actual source and inspected revision. Credit for its methods belongs to its authors. New companions are independently implemented; attribution and the upstream MIT notice are in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md). No unlicensed loop prose or upstream implementation is bundled.
- Neither project is affiliated with this one, and none of them is affiliated with or endorsed by HackerRank.
