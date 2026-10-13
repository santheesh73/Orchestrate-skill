# Adversarial routing

Shape: route, act on or mute incoming messages and media, where some inputs are hostile (scams, impersonation, text that tries to instruct the system). Source: an August 2026 top-40 project with full design docs.

## Architecture that held up

- **Media goes through two separated calls.** The first call only describes or transcribes (images, audio) and is never told what the routing options are. Its result is wrapped as data before the second, routing call sees it, so an instruction hidden in an image reaches the router as a quoted description of that image.
- **Rules in priority tiers:** safety overrides first, then authority to pay or act, then guards, then caps and floors, and last the model's suggestion as the fallback. **A cap wins over a floor**; exactly one guard, documented, may exceed a cap. When a floor loses, the trace keeps it and marks it overridden.
- **Evidence ids are chosen from a list, not written.** Code ranks the receiver's own past items in tiers and picks from that shortlist; assertions check that each item belongs to the receiver and predates the current message. The model never types an id.
- **Confidence computed in code** from named features. Report calibration; never optimize it.
- **Reasons assembled from a small clause grammar,** then checked for register (within length limits, a single sentence, no identifiers). A reason that breaks the check fails its row; cutting it short instead would quietly turn it into a false explanation.

## Guards that fit

- **Wrap untrusted content in a random, per-run nonce fence.** Should the hostile text include the fence marker, escape it and log the event by hash only; the content itself never goes in the log.
- **Text that tries to command the system triggers its own rule.** The perception step flags any attempt to steer the router, and that flag forces a hard override regardless of whether the embedded claim happens to be accurate.
- **Ignore file extensions.** Identify the format from the file's leading bytes. One corpus had wrong extensions on over half of its media files.
- **Explicit failure dispositions** (ABORT / DEGRADE / FAIL ROW) with distinct exit codes. Budget exhaustion is ordered: completed calls are cached, so a rerun pays only for the remainder.
- **Cache keyed by content hash, included in the submission,** plus an `assert-identical` check comparing the output of two runs.

## Grounding tests

- **Threat-model test:** inject an instruction into a message and prove the rules that do not read message text cannot change.
- **Ablation:** remove each input a rule declares in its `reads` set; the rule must stop firing.

## Where rows are lost

- Boundary between "mute as scam" and "act with caution". The fix that worked was resolved definitions in the prompt, not a threshold tuned against 30 rows.
- The confidence column, the most volatile under re-derivation because it was a sum with no thresholding. Measure the noise floor before trusting a one-row change.
