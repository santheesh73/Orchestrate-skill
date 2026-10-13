# Retrieval and triage

Shape: answer, route or escalate each request using a provided document corpus. Source: the May 2026 #1 repo and write-up, read in code.

## Architecture that held up

- **Single agent, one tool with three modes: search, read, grep.** A short fixed flow in the prompt (search, then read the article, then answer), a hard cap of about 8 tool calls, and a recursion limit. Built on a framework agent (`create_agent`); the loop is still one findable place.
- **Hybrid retrieval.** BM25 plus dense embeddings fused with reciprocal rank fusion, then a cross-encoder rerank. Deterministic chunking with stored character offsets so every snippet traces to a source span.
- **Typed filters** (company, product area, breadcrumb substring) translated to a safe query; unknown values are dropped silently instead of erroring.
- **Pre-model short-circuits in a fixed order:** empty ticket, pleasantry or thanks, clearly out of scope, prompt injection (regex, multilingual), too vague to act on. Each gets a canned, correct response with no model call.
- **Small model for tagging** (language normalization, company hint), cached on disk; the stronger model only in the agent.
- **Structured decision object** with literal enums for status and request type, a normalized product-area slug, the response, a one-to-three-sentence justification, and cited paths. Off-enum values are clamped to a safe value.

## Guards that fit

- **Citation guard** (the standout idea): after the agent returns, compare cited paths with paths actually read this turn. Drop unread citations and record the drop on the trace. If nothing verified was cited and nothing was read, downgrade to escalation with a canned message and say so in the justification. If evidence was read but the wrong path cited, keep the reply and flag a mismatch. Exempt pleasantries and invalid requests.
- **Escalation contract in the prompt:** escalate on high risk, sensitive data, override demands, identity theft or fraud, or thin evidence, with BAD and GOOD acknowledgement examples. A code step caps escalation text length (about 35 words).
- **Failure ladder:** any exception, recursion-limit hit or missing structured output becomes an honest escalation row, with a per-row JSON trace (tool calls, reads, dropped citations, flags).

## Grounding test

Remove the article the agent cited from the corpus and rerun that row. The reply must change or escalate. If it does not, the answer was coming from the model's priors, not the corpus.

## Where rows are lost

- Close taxonomy pairs (two product areas that overlap). Fix with **contrastive examples** in the prompt (when to pick each), not a bare list.
- Over-escalation drifting toward all-escalate, which is invalid. Watch the distribution.
- Generic replies that would fit any ticket. Quote the specific step or policy from the read article.
