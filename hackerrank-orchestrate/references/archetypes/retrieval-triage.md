# Retrieval and triage

Shape: answer, route or escalate each request using a provided document corpus. Source: the May 2026 #1 repo and write-up, read in code.

## Architecture that held up

- **A single agent with a single tool that has a search mode, a read mode and a grep mode.** A short fixed flow in the prompt (search, then read the article, then answer), a hard cap of about 8 tool calls, and a recursion limit. Built on a framework agent (`create_agent`); the loop is still one findable place.
- **Hybrid retrieval.** Lexical BM25 and dense-embedding results are merged by reciprocal rank fusion and then reordered by a cross-encoder. Chunk boundaries are deterministic and each chunk keeps its character offsets, so any snippet maps back to an exact span of its source.
- **Typed filters** (company, product area, breadcrumb substring) translated to a safe query; unknown values are dropped silently instead of erroring.
- **Short-circuits before any model call, checked in a set order:** an empty ticket, a greeting or thank-you, an obviously off-topic request, an injection attempt (regex patterns in several languages), and a request too vague to act on. Each gets a canned, correct response with no model call.
- **Small model for tagging** (language normalization, company hint), cached on disk; the stronger model only in the agent.
- **Structured decision object** holding status and request type as literal enums, a normalized product-area slug, the reply, a justification of one to three sentences, and the cited paths. Off-enum values are clamped to a safe value.

## Guards that fit

- **Citation guard** (the strongest idea in the repo): once the agent finishes, check each cited path against the paths it actually opened on that turn. Remove citations to unopened documents and note the removal in the trace. When no verified citation is left and nothing was opened, turn the row into an escalation with a fixed message, and the justification states that this happened. If evidence was read but the wrong path cited, keep the reply and flag a mismatch. Exempt pleasantries and invalid requests.
- **Escalation contract in the prompt:** escalate on high risk, sensitive data, override demands, identity theft or fraud, or thin evidence, with BAD and GOOD acknowledgement examples. Code then trims escalation text to a maximum (about 35 words).
- **Failure ladder:** an exception, a recursion-limit stop or an absent structured answer each produce an honest escalation row, and every row writes a JSON trace (tool calls, documents opened, citations removed, flags).

## Grounding test

Remove the article the agent cited from the corpus and rerun that row. The reply must change or escalate. If it does not, the answer was coming from the model's priors, not the corpus.

## Where rows are lost

- Close taxonomy pairs (two product areas that overlap). Fix with **contrastive examples** in the prompt (when to pick each), not a bare list.
- Over-escalation drifting toward all-escalate, which is invalid. Watch the distribution.
- Generic replies that would fit any ticket. Quote the specific step or policy from the read article.
