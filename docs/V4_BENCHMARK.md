# V4 benchmark scope and evidence

Own baseline revision: 76c928eedce69fb62cc33a81c18349d37b14b53f. Measurements were
recorded before publication; the report preserves that working-tree state and
source hashes rather than inventing a release commit. Reference source revision:
ccb175f8717f67fd084c57d853076f0b95636980, confirmed against remote HEAD on 2026-10-24.

The existing independent fixture framework was reused. It does not modify the
reference implementation or fetch hidden official data. Current own-only run:

| Category | Healthy | Defective | False positives | False negatives | Unknown |
|---|---:|---:|---:|---:|---:|
| Packaging | 4 | 15 | 0 | 0 | 0 |
| Decision-ID audit | 5 | 3 | 0 | 0 | 0 |

These are small known synthetic fixtures, not a claim of perfect real-world
detection. Healthy cases provide a false-positive denominator; injected cases
provide a false-negative denominator. Unsupported policies have separate N/A
accounting. Single-run durations, fixture fingerprints, exact checker hashes,
environment and installation-conflict results are in [the JSON report](v4-comparison.json).
The uncommitted V4 source/test/resource snapshot is bound separately by
[the candidate source manifest](v4-source-manifest.json).

## What is and is not compared

| Dimension | Current evidence |
|---|---|
| Contract defects and blocker detection | Own run on identical framework fixtures; fresh reference run UNKNOWN |
| False-positive/negative rates | Own measured denominators above; no fresh reference rates claimed |
| Installation conflict preservation | Own temporary-project run; reference source inspected only |
| Skill activation reliability | UNKNOWN for both; no genuine paired live trials supplied |
| Runtime | Own one-run fixture timings only; no fresh cross-repository speed comparison |
| Reproducibility | Fingerprints and deterministic fixture inputs; no official hidden-data guarantee |
| Documentation usability | Local-link checks and exercised own examples; no participant usability study |

Automatic approval review rejected executing the pinned external repository's
checker/installer code because execution authorization and isolation were not
established. That action has not been retried or performed indirectly. A fresh
reference-runtime comparison remains incomplete pending explicit approval. Static
source observations are recorded in the audit and are not substituted for runtime evidence.

Reproduce the safe own-only run with a new report filename:

```text
python benchmarks/comparison/run.py --own-leakage-audit decision_ids --report comparison-v4-local.json
```

The framework retains its opt-in reference execution interface for a separately
approved run, confined to disposable synthetic projects. No overall superiority
claim is supported by the current V4 evidence.
