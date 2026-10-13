# Optional: the community toolkit

`hackerrank-orchestrate-skills` is a community repository (not affiliated with HackerRank or with this skill) with auto-triggering skills and a zero-dependency Python CLI that audits a submission repo. **This skill never depends on it:** `self-score.md` Path A is a complete gate without it.

**Secondhand digest.** The toolkit repository could not be located from here on 2026-10-13. This page restates, in its own words, the toolkit as described by [orchestrate-loop](https://github.com/bsrikumar855-dot/orchestrate-loop), which read it at a commit titled "Phase 2: experiment tracker + live score delta loop". Commands may have changed; trust the toolkit's own `--help` over this page.

## Install (if the user has it)

```bash
cd hackerrank-orchestrate-skills
pip install -e .
python -m orchestrate_kit memory seed
python -m orchestrate_kit selftest
```

`python -m orchestrate_kit` works without PATH changes. Don't copy its skills next to this one unless the user wants both; overlapping triggers compete.

## CLI

| Command | Purpose |
|---|---|
| `evaluate <repo>` | Is it shippable? Blockers print first; exit 2 on any blocker |
| `certify <repo>` | Stricter: anything above INFO fails (exit 3) |
| `release <repo>` | Final gate with manual items; the last is the authorship attestation only the participant can make |
| `selftest` | Plants known defects and checks the audits catch them, plus clean cases that must stay quiet |
| `mentor "<proposal>"` | Pre-mortem before building; prints UNKNOWN instead of guessing a gain |
| `memory why-not / recall / list / search / verify / add` | Rejection log; adding a rejection requires a reconsider-if condition |
| `interview --persona … --difficulty … [--panel]` | Judge simulator; scores the shape of answers, not their truth |
| `transcript analyze <file>` / `compose "<goal>" --stage …` | Lint a transcript against the published dimensions; fill a prompt blueprint |
| `score --repo . [--what-if …]` | Estimated four-artifact scoreboard with local history; not a real score |
| `experiment start / finish / list / compare / frontier / next / plan` | Baseline, change, measure, accept or reject; the tool form of the change-record loop |
| `viz all --out diagrams/` | Generated architecture diagrams |

Confidence labels on every finding: **measured / observed / inferred / unknown**. A skipped audit is unknown, never a pass.

## The 20-rule playbook, one line each

Evidence: 1 no improvement until a number moves · 2 measure blast radius, not just the win · 3 prove the counterfactual · 4 compute the ceiling first · 5 a rejection is a deliverable.
Auditing the audit: 6 run a negative control against the test itself · 7 an audit never changes what it audits · 8 measure at the scale and conditions you will run in.
Regression: 9 pin the output hash and log every re-pin with its cause · 10 keep tests hermetic (no credentials, each file passes alone) · 11 state where each guarantee stops.
Unseen data: 12 hunt sample coupling (rename ids, reformat timestamps, shuffle rows, sniff file types by bytes, review terms that fire on one row) · 13 separate specified from observed constants · 14 calibrate to the labeling policy, not an ideal.
Release: 15 rehearse a fresh clone using only the README · 16 generated files are stale until regenerated · 17 docs are production code.
Reporting: 18 label VERIFIED / MEASURED / INFERENCE / UNKNOWN · 19 name the limitation before you are asked · 20 stop when everything fixable is fixed or what remains is precisely named.

## Release gate, cheapest checks first

0. Clean working tree; regenerate artifacts to a temp path and compare hashes; fresh clone following only the README; each test file passes alone.
1. Literal spec conformance: column names and order, separators, allowed values, one output per input. (`scripts/preflight.py`)
2. Evidence for each change: metric, gain and cost, blast radius, counterfactual, ceiling, logged rejections.
3. Trust the tests: negative controls; audits never write to ground truth; diff every artifact after the full suite.
4. Regression: golden hash pinned; every fixed defect has a test that fails without the fix.
5. Unseen-data robustness and `CONSTANTS.md` provenance. (`scripts/interview_drill.py`)
6. Determinism across repeated runs and processes, with the boundary stated. (`scripts/rerun_diff.py`)
7. Security: injection, path traversal, failure paths that still produce valid output, no secrets.
8. Docs: every number re-derived today; limitations first.
9. Verdict: READY or NOT READY with the named blocker.

## Caveats

- Its scores measure the shape of work, not correctness, and not a real HackerRank score. Never quote them as predictions.
- Its case-study numbers come from a different edition and dataset; treat them as method examples.
- Where its playbook and this skill differ, `evaluation.md` is canonical.
