# Multimodal verification

Shape: decide whether a claim is supported, contradicted or unverifiable from images or scanned documents. Source: a June 2026 top-3 project with full design docs.

## Architecture that held up

- **The vision model looks closer through a zoom tool.** Before it reports, it may request a crop by quadrant, by an object alias or by coordinates. A request for a region that does not exist gets the middle of the image and an explanatory note rather than an error. After roughly 6 rounds the loop demands the final answer.
- **Typed seam.** A single typed object is all the decision code ever receives from the model. Its enums live in one place, the tool schema and the validator are derived from them, and a test compares them with the lists in the problem statement.
- **Verdict function in pure code** over the perception record. History can only add things, such as review flags; it cannot alter the verdict, and the reason is structural: the verdict function has no history parameter.
- **Design review before coding** with severity-tagged findings and a complexity audit; every component names the failure it prevents. A tool that failed that test was demoted to plain code.

## Guards that fit

- **Return "not enough information" when the evidence is insufficient,** and do not base it on a vague authenticity signal. Where the rule given in the spec disagreed with a labeled row, the author chose the more cautious condition and logged the departure as an unresolved decision rather than settling it quietly.
- **Detect recycled photos.** Hashing every image exposes one photo submitted with several claims. Key the cache on the file's content hash; a path can change.
- **Vote across three runs, but only for borderline readings.** That raises the per-row cost a little. The author reported the expensive error class improving across two separate runs; treat the causal link as their claim and measure variance first.
- **Justifications generated from logged facts** (the cue, the branch, the rule), with a deterministic template fallback.
- **Input columns copied to the output byte for byte,** written with Python's standard `csv` module as fully quoted UTF-8, and covered by a write-then-read test.

## Grounding tests

- **Blank-drop:** substitute an empty image; the answer must fall back to "not enough information". If a claim still gets approved with no picture, the agent was reading the text and ignoring the image.
- **Swap:** give the row a different image; the output must change.

## Where rows are lost

- The model's default proposal near the supported versus unverifiable boundary. Write resolved definitions with contrastive examples (`output-csv.md` §2).
- Downsampled images losing the detail that decides the claim. Downsample context, keep the claimed region at full resolution.
- Cost creep from repeated calls. Track per-row cost and prompt-cache the stable prefix.
