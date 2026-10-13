# Winning approaches

Cross-cutting patterns from public top-finisher material. Problem-specific patterns are in `archetypes/`; leaderboard calibration is in `rubric.md` §5.

**Evidence limits, read first.** Sources reachable so far: the May 2026 #1 repo and write-up ([code](https://github.com/saai-syvendra/hackerrank-orchestrate), [write-up](https://saai.syvendra.com/myspace/hackerrank-orchestrate)), a June 2026 top-3 project and an August 2026 top-40 project (both with full design docs), the organizer's post-mortem, the official starter repos, and a first-hand September 2026 interview write-up. The June, August and September #1 repos were not found. Treat everything below as habits that top finishers shared, not as proven causes of their ranks. The organizer's post-mortem itself credits behavior (weighing tradeoffs, showing evidence, owning decisions) over any particular tool or stack.

## 1. The master pattern: the model observes, code rules

- The model's job is to fill in a **typed record of what it saw**: a suggested label, a shortlist of candidates, true/false answers to specific questions about the evidence. The binding answer is not part of that record.
- Deterministic functions map the record onto the output columns by walking a prioritized **rule table**. Each row's trace names the winning rule and every rule that matched but lost.
- What this buys you, each item both testable and worth saying in the interview:
  1. **Repeatable.** Store each record in a cache; a `--from-cache` flag replays the decision code with no API traffic at all.
  2. **Auditable.** You can follow any output cell back to one rule id and the observation it consumed.
  3. **Injection-resistant by construction.** A hostile input can spoil the observation it lands in, nothing more; the decision code never reads raw input.
  4. **Constraints live in signatures.** If history may raise caution but must never change the verdict, the verdict function simply does not take history as a parameter. No prompt wording is needed.
- **Each rule lists what it reads** (a `reads` set). Two tests guard that boundary: a threat-model test shows that hostile text never arrives at a rule whose `reads` excludes it, and an ablation test deletes each listed input in turn and checks that the rule no longer matches.
- **Keep two kinds of error apart.** Type A lives in your rules or code: it is deterministic, and once fixed you can re-grade from the cache for free. Type B is a wrong observation from the model: only a paid re-run helps, so collect them and re-run in one batch. Budget usually leaks when someone re-runs the model over and over to cure what was really a Type A bug.
- **Honest limit.** The pattern wins code and interview credit, but it cannot rescue a model that misjudges borderline rows. Leave time for `output-csv.md` §2 too.

## 2. Patterns that recur across winners

- **Single agent with tools** led the May top 10 (7 of 10). Start there for problems that need reasoning across several pieces of evidence, and move away only on measured grounds. One first-hand account reports a single agent that held the whole evidence set outperforming a multi-agent design that passed summaries between agents.
- **Guards with their own archetype pages:** pre-model short-circuit rules and the citation guard (`archetypes/retrieval-triage.md`), nonce-fenced untrusted content and a content-addressed cache shipped with the submission (`archetypes/adversarial-routing.md`), blank-drop and swap grounding tests (`archetypes/multimodal-verify.md`).
- **Typed seam.** Define every enum once, in one schema module. Derive the tool schema and the output validator from that module, and keep a unit test that compares its literals with the lists in the problem statement.
- **Cheap model for tagging, stronger model where it matters.** Put the unchanging prompt prefix in the prompt cache, then check the logs for a cache-read token count above zero.
- **Cost is a first-class number,** tracked per row. Since September 2026 it is also a required deliverable (`usage_report.md`).
- **Fewer components you can explain.** One June author had earlier built a 15-stage pipeline that landed mid-table, because nobody could show what each stage contributed; a smaller design with measured parts placed far higher. Remove any part you cannot connect to a specific failure it stops.

## 3. Design-doc suite (one to two hours at the start)

Short, cross-checked, one source of truth. In the transcript it shows planning; in the interview it becomes your notes. Keep the reasons that matter for grading in code comments too, since the code grader reads only source.

1. Problem analysis, including places the spec contradicts itself and how you resolved them
2. Dataset analysis (facts only)
3. Generalization policy (`evaluation.md` §1)
4. Threat model: which inputs an attacker controls, and which functions are allowed to see them
5. Failure modes: for each one, its symptom, the place it is detected, the fallback behavior, and its disposition
6. System design, plus the rule table with each rule's `reads` set
7. How you will evaluate: gates, the noise floor, the resolution table
8. Design review: severity-tagged findings and a complexity audit
9. Decision log with who decided (`assets/decision_log.md`)

## 4. Do and do not

| Do | Do not |
|---|---|
| Use the model to observe; make binding decisions in pure functions with tests | Let the model produce the final label, figure or evidence id |
| Key cached model records by a hash of their inputs, and include the cache in the submission | Call the model again and again until a number looks better |
| Allow a citation only if the full document was actually opened | Cite something you saw only as a search snippet |
| Show each input matters by removing or swapping it (blank-drop, swap, ablation) | Assert that a rule depends on an input when no test takes it away |
| Escalate when evidence is weak or the row errored, and say why | Invent a confident answer, let one row crash the run, or escalate every row |
| Decide in advance what happens on each kind of failure | Leave a half-written output file behind |
| Measure the noise floor a single time and reuse it | Treat a change in one row as a win or a loss |
| Keep rationale in source | Rely on README claims for code points |
| Reserve time for output rows and justifications | Treat the CSV as solved because the code is strong |
