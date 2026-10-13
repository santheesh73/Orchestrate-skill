# Multimodal verification

Shape: decide whether a claim is supported, contradicted or unverifiable from images or scanned documents. Source: a June 2026 top-3 project with full design docs.

## Architecture that held up

- **Perception is a tool loop with a zoom.** The vision model can crop or inspect a named region (quadrants, object aliases, or coordinates) before reporting. An invalid region returns a center crop plus a note, not an error. Cap rounds (about 6), then force a final answer.
- **Typed seam.** One object is the only bridge from the model to the decision code. Enums are defined once; the tool schema and validator are generated from them; a test asserts they equal the problem statement's lists.
- **Verdict function in pure code** over the perception record. History is an additive overlay only: it can add review flags but never change the verdict, enforced by never passing history to the verdict function.
- **Design review before coding** with severity-tagged findings and a complexity audit; every component names the failure it prevents. A tool that failed that test was demoted to plain code.

## Guards that fit

- **Gate "not enough information" on evidence sufficiency,** not on a soft authenticity flag. When a prescribed rule conflicted with a ground-truth row, the author adopted the safer gate and wrote the deviation down as an open decision instead of deciding silently.
- **Fingerprint reused media.** Hash each image so the same photo reused across claims is detectable. Cache by content hash, never by path.
- **Majority vote only on borderline reads.** Three runs on borderline cases cost modestly more per row. The author reported the expensive error class improving across two separate runs; treat the causal link as their claim and measure variance first.
- **Justifications generated from logged facts** (the cue, the branch, the rule), with a deterministic template fallback.
- **Byte-exact echo of input columns** via the stdlib CSV module, all-quoted UTF-8, and a round-trip test.

## Grounding tests

- **Blank-drop:** replace the image with a blank; the verdict must collapse to "not enough information". A vision agent that approves a claim with a blank image was matching text, not pixels.
- **Swap:** give the row a different image; the output must change.

## Where rows are lost

- The model's default proposal near the supported versus unverifiable boundary. Write resolved definitions with contrastive examples (`output-csv.md` §2).
- Downsampled images losing the detail that decides the claim. Downsample context, keep the claimed region at full resolution.
- Cost creep from repeated calls. Track per-row cost and prompt-cache the stable prefix.
