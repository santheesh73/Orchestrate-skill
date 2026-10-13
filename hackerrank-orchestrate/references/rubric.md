# How Orchestrate is scored

**Check the live challenge page first.** Weights and sub-criteria below come from organizer material for earlier editions and can change. When they disagree, the live page wins.

Sources:
- [HackerRank: Behind the Scenes of Orchestrate](https://www.hackerrank.com/blog/behind-the-scenes-of-hackerrank-orchestrate/) (organizer post-mortem, May 2026 edition)
- The May 2026 evaluation criteria, as copied in the [May #1 repo](https://github.com/saai-syvendra/hackerrank-orchestrate)
- Official starter repos, for example [september26](https://github.com/interviewstreet/hackerrank-orchestrate-september26)

## Contents
1. Top-level weights
2. Sub-criteria per artifact
3. Caps, invalid strategies and tie-breaks
4. Where effort pays
5. What the leaderboards show

## 1. Top-level weights

| Artifact | Weight |
|---|---|
| Code zip | 30 |
| Output CSV | 30 |
| AI judge interview | 30 (about 30 minutes, camera on, opens after submission within a fixed window) |
| AI chat transcript | 10 |

## 2. Sub-criteria per artifact

| Artifact | Sub-criteria (share of that artifact's score) |
|---|---|
| Code zip | Agent architecture 30% · prompt and tool craft 30% · robustness 25% · engineering rigor 15% |
| Output CSV | Per-row accuracy against a hidden golden set, plus a separate adversarial safety score |
| Interview | Technical depth and ownership 40% · problem understanding and judgment 25% · communication 20% · honesty 15% |
| Transcript | Direction and architecture ownership 35% · technical specificity 25% · iteration and verification 25% · safety and edge cases 15% |

What the code grader looks for (May criteria): separation of concerns, grounding in the provided corpus, a clear escalation path, seeded or deterministic sampling, pinned dependencies, a runnable README in the code package, and secrets read from environment variables.

What the interview looks for (May criteria): the participant can **clearly distinguish what they designed from what an AI tool generated**.

## 3. Caps, invalid strategies and tie-breaks

- **Source only.** "We reward only what is observable in the source code." README claims earn nothing in the code score.
- **Generic justifications are capped.** A row with the right label and a generic justification tops out around 70% for that row.
- **Escalating or refusing everything is invalid.** A safe-looking all-escalate output does not score.
- **Short interview answers score low.** The organizer measured a correlation of about -0.57 between short answers and interview score.
- **Tie-break order:** interview, then code, then output CSV, then transcript.

## 4. Where effort pays

| Artifact | Spend effort on | Because |
|---|---|---|
| Code | A findable, named agent loop; tool descriptions and prompts as first-class files; then robustness | Architecture plus prompt and tool craft is 60% of the code score; engineering rigor is 15% |
| Code | Rationale in docstrings and comments beside constants | Only source is read |
| Output CSV | Boundary calls and specific, evidence-anchored justifications | Generic justifications are capped; the CSV is the usual weak stage for top finishers |
| Interview | Long, specific answers about your own decisions | Depth and ownership is 40%; short answers correlate with low scores |
| Transcript | Stating the plan, choosing architecture yourself, verifying out loud | Ownership 35%, iteration and verification 25% |

## 5. What the leaderboards show

Computed from public leaderboards for the May, June and August 2026 editions. Calibration, not targets.

- **Balance wins.** Most of each top 50 sat in the top quartile on all four stages (37 of 50 in May, 33 in June, 41 in August). The organizer reports every top-10 finisher was top quartile on all four.
- **Output CSV is the usual weak stage at the top.** It was the weakest stage for 49 of the June top 50 and 34 of the August top 50.
- **Transcript and interview are cheap points.** Field medians are roughly 1.4 to 3.8 of 10 for transcript and 11 to 15 of 30 for interview, while top-50 averages are 63% to 89% of the maximum.
- **Architecture at the top.** A single agent with tools led the top 10 (7 of 10); graph or state-machine designs had the best average rank. Claude Code users were about 44% of the top 50 versus about 14% overall, but the organizer attributes results to behavior, not the tool.
- **What interviewers rewarded:** specific decisions with tradeoffs, test evidence and regressions, safety claims that match the code, visible ownership. **Penalized:** generic answers, unsupported safety claims, answers that contradict the implementation.
