# The AI judge interview

30 points and the first tie-breaker. Sub-criteria (May 2026): technical depth and ownership 40%, problem understanding and judgment 25%, communication 20%, honesty 15%. Short answers correlate with low scores. Check the live rules for what is allowed during the interview.

## 1. What the judge asks

It asks about **your** code, not about agents in general. First-hand examples from September 2026: "Which statistic estimates variable spend?", "On the same date, which is applied first, the debit or the credit?". One participant answered "debits first" when the code did credits first and lost points for contradicting the implementation. Generic prep missed these.

Topics probed across editions: high-level architecture, deterministic versus model reasoning, the end-to-end flow of one row, retrieval, confidence, escalation, the AI-assisted workflow, tradeoffs, limitations.

## 2. Build the question bank from your code

```
python scripts/interview_drill.py code/ --constants CONSTANTS.md --out drill.md
```

It lists every named constant, numeric threshold, sort key and comparison gate with its file:line, plus constants missing from `CONSTANTS.md`. For each question, open the line, then answer out loud. If your answer and the code disagree, the code is the truth; fix your answer, or fix the code and rerun.

Add by hand:
- Walk one real row end to end, naming each module and real field names in order.
- The three rejected changes you are proudest of, with the numbers that killed them.
- Two limitations to volunteer.
- Where the determinism guarantee stops.

## 3. Answer shape

Decision → alternative rejected → evidence → limitation. At least four sentences, never one line.

Illustrative example (the figures are placeholders; use your own measured ones):

> "I estimate variable spend with the median over a bounded window because a single large purchase skews the mean. I tried the mean first; it overshot on users with one-off purchases, which I saw in the full-output diff, [N] rows moved. The median is conservative for users whose spending is rising, which is a known limitation. It is in CONSTANTS.md as JUDGEMENT, not tuned."

Weak to strong:

| Question | Weak | Strong |
|---|---|---|
| Why that number? | "It worked best." | Provenance label, the losing alternative, the evidence. |
| Is it deterministic? | "Yes." | "Given the cached model record, yes; the live provider call is not, and here is the measured noise floor." |
| Did you overfit? | "No." | The finding / principle / refused-rule triples. |
| What's your accuracy? | A bare percentage. | The set, its size, and that one row is 3 to 5 points. |
| More time? | "Polish." | The specific uncertainty and the experiment that resolves it. |

## 4. Ownership and honesty

- Say "I chose X because…", not "Claude built…". Be precise about which parts the AI generated and which you designed; the criteria ask you to distinguish them. `assets/decision_log.md` is the source.
- "I don't remember the exact value, but here is how it was chosen" is a good answer. A confident wrong one is not.

Claims never to make unless directly supported: "I wrote every line myself"; unqualified "deterministic"; "100%" without the set and size; "no dataset-specific assumptions" without the corpus-literal test; "handles every attack"; "tests prove it generalizes"; "it will rank well"; "incremental commits" without reading `git log` first.

## 5. Hour-before checklist

- `CONSTANTS.md` read aloud.
- Drill file answered against the code.
- One row traced end to end.
- Three rejections memorized with numbers.
- Boundary sentence for every guarantee.
- `git log` read.
- Two limitations chosen to volunteer.
- Sleep protected; do not rehearse for the first time under deadline pressure.
