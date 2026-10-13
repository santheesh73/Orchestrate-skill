# How Orchestrate is scored

**Check the live challenge page first.** Everything below comes from material on earlier editions and can change; the live page wins.

Evidence labels: **VERIFIED** = read in the linked source on 2026-10-13. **INFERRED** = taken from a secondary source that could not be re-checked here. **UNKNOWN** = not available.

Sources:
- [HackerRank: Behind the Scenes of Orchestrate](https://www.hackerrank.com/blog/behind-the-scenes-of-hackerrank-orchestrate/) (organizer post-mortem of the May 2026 edition)
- The May 2026 evaluation criteria (`evalutation_criteria.md`, sic) in the [May #1 repo](https://github.com/saai-syvendra/hackerrank-orchestrate)
- Official starter repos, for example [september26](https://github.com/interviewstreet/hackerrank-orchestrate-september26)
- Per-stage leaderboard percentages from [orchestrate-loop](https://github.com/bsrikumar855-dot/orchestrate-loop), which computed them from public leaderboard data

## Contents
1. Top-level weights
2. Sub-criteria per artifact
3. Caps, invalid strategies and tie-breaks
4. Where effort pays
5. What the leaderboards show

## 1. Top-level weights

Final score = 0.10 × transcript + 0.30 × interview + 0.30 × output CSV + 0.30 × code zip (VERIFIED, post-mortem).

| Artifact | Weight |
|---|---|
| Code zip | 30 |
| Output CSV | 30 |
| AI judge interview | 30 (a 30-minute voice interview, VERIFIED; camera and scheduling window per the live page, UNKNOWN here) |
| AI chat transcript | 10 |

## 2. Sub-criteria per artifact (VERIFIED, post-mortem)

| Artifact | Sub-criteria (share of that artifact's score) |
|---|---|
| Code zip | Agent architecture 30% · prompt and tool craft 30% · agent robustness 25% · engineering rigor 15% |
| Output CSV | Per-row correctness against a hidden golden set; the judge also assigns one 0–100 safety score for the submission as a whole. No sub-weights are published. |
| Interview | Technical depth and ownership 40% · problem understanding and judgment 25% · communication clarity 20% · honesty and self-awareness 15% |
| Transcript | Direction and architecture ownership 35% · technical specificity and constraint 25% · iteration and verification 25% · safety, edge case and quality awareness 15% |

What the code grader looked for (VERIFIED, May criteria): separation of concerns (retrieval, reasoning, routing, output), grounding in the provided corpus, explicit escalation logic, seeded sampling, pinned dependencies, a runnable `code/README.md`, secrets read from environment variables. The interview criteria ask you to **clearly distinguish what you designed from what an AI tool generated**.

## 3. Caps, invalid strategies and tie-breaks (VERIFIED, post-mortem)

- **Source only.** "We reward only what is observable in the source code." README claims, comments describing intent and unused imports don't count toward the code score. A runnable README still matters for reproducibility.
- **Generic justifications are capped** at about 70 for that row, even when the action is right.
- **Escalating everything was invalid; so was replying to everything.**
- **Interview length matters.** Against interview score: very short answers r = −0.568; total candidate words r = 0.615; share of longer answers r = 0.631; number of candidate turns weakly negative (no value published).
- **Tie-break order:** interview, then code zip, then output CSV, then transcript.

## 4. Where effort pays

| Artifact | Spend effort on | Because |
|---|---|---|
| Code | A findable, named agent loop; prompts and tool descriptions as first-class files; then robustness | Architecture plus prompt and tool craft is 60% of the code score; engineering rigor is 15% |
| Code | Rationale in docstrings and comments beside constants | The grader reads behavior in source, not README claims |
| Output CSV | Boundary calls and specific, evidence-anchored justifications | Generic justifications are capped; top finishers most often lose ground on the CSV |
| Interview | Long, specific answers about your own decisions | Depth and ownership is 40%; very short answers correlate with low scores (r = −0.568) |
| Transcript | Stating the plan, choosing architecture yourself, verifying out loud | Ownership 35%, iteration and verification 25% |

## 5. What the leaderboards show

Calibration, not targets.

**Organizer findings (VERIFIED, post-mortem, May edition):**
- 1,349 participants submitted all four artifacts; no pair of metrics had a rank correlation above 0.45, so no single artifact predicts the leaderboard.
- Every top-10 candidate was in the top quartile on all four metrics.
- Top-10 architectures: single agent with tools or RAG 7, multi-stage or multi-agent pipeline 2, graph or state-machine workflow 1. Average rank by architecture was best for graph or state-machine workflows (351) versus multi-stage pipelines (468) and single agents (592).
- Claude Code was used by 44% of the top 50 versus 14.4% of all transcripts. The organizer attributes results to behavior (tradeoff reasoning, evidence, ownership), not the tool.

**Per-stage averages of top finishers (INFERRED).** Average score as a percentage of each stage's maximum for the top 1 / top 10 / top 50. Computed by orchestrate-loop from public leaderboard data; the leaderboard API was not reachable from here to re-derive them.

| Edition (field) | Total at #1 / #10 / #50 | Transcript | Interview | Output CSV | Code zip |
|---|---|---|---|---|---|
| May (1,349 VERIFIED) | 76.0 / 72.3 / 65.4 | 82 / 78 / 63 | 62 / 70 / 64 | 76 / 69 / 69 | 88 / 80 / 76 |
| June (1,773) | 72.5 / 67.5 / 63.3 | 65 / 87 / 86 | 84 / 75 / 72 | 45 / 48 / 46 | 91 / 79 / 74 |
| August (1,983) | 84.2 / 80.8 / 74.0 | 89 / 95 / 89 | 87 / 82 / 80 | 77 / 70 / 68 | 87 / 89 / 82 |

Readings from the same data (INFERRED):
- **Balance wins.** In every edition, a majority of the top 50 placed in the top quarter of the field on each of the four stages (May 37 of 50, which the post-mortem confirms, VERIFIED; June 33 and August 41, INFERRED).
- **The output CSV is the usual weak stage at the top.** It was the weakest stage for 49 of the June top 50 and 34 of the August top 50.
- **Transcript and interview are cheap points.** Field medians were roughly 1.4 to 3.8 of 10 for transcript and 11 to 15 of 30 for interview.

Interview patterns (VERIFIED, post-mortem): candidates who gave more substantial explanations tended to score higher, and, as a separate finding, specificity (tradeoffs, examples and implementation details) correlated with interview score at r = 0.583. Weak candidates often contradicted the code or stayed vague, and the number of candidate turns had a weak negative correlation with interview score.
