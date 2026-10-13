# Winning approaches

Cross-cutting patterns from public top-finisher material. Problem-specific patterns are in `archetypes/`; leaderboard calibration is in `rubric.md` §5.

**Evidence limits, read first.** Sources reachable so far: the May 2026 #1 repo and write-up ([code](https://github.com/saai-syvendra/hackerrank-orchestrate), [write-up](https://saai.syvendra.com/myspace/hackerrank-orchestrate)), a June 2026 top-3 project and an August 2026 top-40 project (both with full design docs), the organizer's post-mortem, the official starter repos, and a first-hand September 2026 interview write-up. The June, August and September #1 repos were not found. These are patterns top finishers used, not proof each one caused the rank. The organizer's own conclusion is that behavior (tradeoff reasoning, evidence, ownership) drove results more than any tool or stack.

## 1. The master pattern: the model describes, code decides

- The model returns a **structured record of observations** (a proposed label, ranked candidates, yes/no claims about the evidence). It does not return the binding answer.
- Pure functions turn that record into the final columns through an ordered **rule table**. The rule that won, and the rules that fired and lost, are written on the row's trace.
- Benefits, each testable and each a good interview answer:
  1. **Repeatable.** Cache the record; re-run the decision layer offline with zero API calls (a `--from-cache` flag).
  2. **Auditable.** Every column traces to a rule id plus a logged observation.
  3. **Injection-resistant by structure.** Hostile text can at worst corrupt one observation; it cannot reach code that never takes it as input.
  4. **Constraints are structural.** "History may add caution but never flip the verdict" is enforced by leaving history out of the verdict function's inputs, not by a prompt sentence.
- **Rules declare the inputs they read** (a `reads` set). Two tests defend the seam: a threat-model test proves injected text cannot reach rules that do not read it, and an ablation test removes each declared input and requires the rule to stop firing.
- **Separate error classes.** Class A: your code or rules (deterministic; fix and re-grade free from the cache). Class B: the model misperceived (needs a paid re-run; batch these). Most wasted budget is re-rolling Class B hoping to fix Class A.
- **Honest limit.** This pattern earns code and interview points but does not fix wrong boundary calls by the model. Budget time for `output-csv.md` §2 as well.

## 2. Patterns that recur across winners

- **Single agent with tools** led the May top 10 (7 of 10). Default to it for cross-evidence reasoning unless you measured otherwise. One first-hand case found a single agent holding all evidence beat multi-agent summary hand-offs.
- **Pre-model short-circuit rules** in a fixed order (empty, pleasantry, out of scope, injection, too vague) answer with a canned correct response and save a model call.
- **Typed seam.** One schema module defines the enums; the tool schema and output validator are generated from it; a unit test asserts those literals equal the problem statement's lists.
- **Citation guard.** Compare cited evidence with evidence actually read this turn. Drop unread citations; if nothing verified was cited and nothing was read, downgrade to an escalation and say so.
- **Fence untrusted content** with an unguessable nonce; escape the fence token if it appears in the content.
- **Content-addressed cache** keyed by file-bytes hash plus prompt version, shipped with the submission so a reviewer can reproduce the output with no key.
- **Cheap model for tagging, stronger model where it matters.** Prompt-cache the stable prefix and verify the cache-read token count is non-zero.
- **Cost is a first-class number,** tracked per row. Since September 2026 it is also a required deliverable (`usage_report.md`).
- **Fewer components you can explain.** A June author's earlier 15-stage pipeline finished mid-pack because they could not measure why each piece helped; the smaller, measured design did far better. Cut any component you cannot tie to a failure it prevents.

## 3. Design-doc suite (one to two hours at the start)

Short, cross-checked, one source of truth. In the transcript it shows planning; in the interview it becomes your notes. Keep the reasons that matter for grading in code comments too, since the code grader reads only source.

1. Problem analysis, including places the spec contradicts itself and how you resolved them
2. Dataset analysis (facts only)
3. Generalization policy (`evaluation.md` §1)
4. Threat model: what is attacker-controlled, which code can read it
5. Failure modes: failure, how it shows, where caught, what happens instead, disposition
6. System design and rule table with `reads` sets
7. Evaluation strategy: gates, noise floor, resolution table
8. Design review: severity-tagged findings and a complexity audit
9. Decision log with who decided (`assets/decision_log.md`)

## 4. Do and do not

| Do | Do not |
|---|---|
| Keep the model as a perceiver; put binding decisions in tested pure code | Let the model write the final label, number or evidence id |
| Cache model records by content hash; ship the cache | Re-roll the model hoping for a better number |
| Guard citations against what was actually read | Cite documents only seen in snippets |
| Prove inputs matter (blank-drop, swap, ablation) | Claim a rule reads something without a test that removes it |
| Escalate honestly when evidence is thin or the row failed | Fabricate a confident answer, crash the batch, or escalate everything |
| Assign every failure a disposition up front | Write a partial output file |
| Measure the noise floor once | Celebrate or reject a one-row change |
| Put rationale in source | Rely on README claims for code points |
| Reserve time for output rows and justifications | Treat the CSV as solved because the code is strong |
