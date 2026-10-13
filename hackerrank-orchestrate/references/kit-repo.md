# Optional: the community toolkit

`hackerrank-orchestrate-skills` is a community repository (not affiliated with HackerRank or with this skill) with auto-triggering skills and a zero-dependency Python CLI that audits a submission repo. **This skill never depends on it:** `self-score.md` Path A and `scripts/selfcheck.py` are a complete gate without it.

**Secondhand digest.** The toolkit repository could not be located from here on 2026-10-13. This page restates, in its own words, the toolkit as described by [orchestrate-loop](https://github.com/bsrikumar855-dot/orchestrate-loop), which read it at one specific commit (its second development phase, which added an experiment tracker). Commands may have changed; trust the toolkit's own `--help` over this page.

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
| `selftest` | Seeds deliberate defects to confirm each audit reports them, and clean inputs to confirm it stays silent |
| `mentor "<proposal>"` | Pre-mortem before building; prints UNKNOWN instead of guessing a gain |
| `memory` subcommands (`why-not`, `recall`, `list`, `search`, `verify`, `add`) | A log of rejected ideas; each new entry must say what would make it worth revisiting |
| `interview --persona … --difficulty … [--panel]` | Practice judge; it grades how an answer is structured and cannot tell whether it is true |
| `transcript analyze <file>` / `compose "<goal>" --stage …` | Lint a transcript against the published dimensions; fill a prompt blueprint |
| `score --repo . [--what-if …]` | Estimated four-artifact scoreboard with local history; not a real score |
| `experiment start / finish / list / compare / frontier / next / plan` | Baseline, change, measure, accept or reject; the tool form of the change-record loop |
| `viz all --out diagrams/` | Generated architecture diagrams |

Findings are tagged, from strongest to weakest, **measured**, **observed**, **inferred** or **unknown**, and an audit that did not run reports unknown rather than passing.

## The 20-rule playbook, one line each

Paraphrased by theme, numbered as in the toolkit.
- Evidence: (1) a change counts only once a measured number improves; (2) report every row it moved, not only the gains; (3) switch it off to show the effect vanishes; (4) size the possible gain before starting; (5) record rejected ideas as output in their own right.
- Checking the checks: (6) feed each test an input it should fail; (7) audits are read-only; (8) test under the same scale and conditions as the real run.
- Regression: (9) fix a hash of the output and note why each time it is re-fixed; (10) tests need no credentials and run one file at a time; (11) say where each guarantee ends.
- Unseen data: (12) look for sample coupling by renaming ids, changing timestamp formats, reordering rows, detecting file types from bytes and reviewing terms that match only one row; (13) keep spec constants apart from observed ones; (14) match how the labels were actually assigned, not an ideal.
- Release: (15) clone fresh and follow only the README; (16) regenerate generated files before trusting them; (17) treat docs with the same care as code.
- Reporting: (18) give each figure an evidence label; (19) volunteer the limitations; (20) finish when all fixable items are fixed or the rest are named exactly.

## Release gate, cheapest checks first

0. Nothing uncommitted; rebuild the artifacts into a scratch directory and compare hashes; clone fresh and use only the README; run every test file by itself.
1. The spec, read literally: column names and their order, delimiters, permitted values, exactly one output row per input. (`scripts/preflight.py`)
2. Every change backed by evidence: its metric, what it gained and cost, which rows moved, the switched-off comparison, the ceiling, the logged rejections.
3. Tests you can believe: each has an input it must fail; no audit modifies the reference data; all artifacts compared before and after the full suite.
4. Regression: the output hash is pinned, and each bug that was fixed has a test that would fail if the fix were removed.
5. Unseen-data robustness and `CONSTANTS.md` provenance. (`scripts/corpus_literals.py`, `scripts/interview_drill.py`)
6. Determinism across repeated runs and processes, with the boundary stated. (`scripts/rerun_diff.py`)
7. Security: injection, path traversal, failure paths that still produce valid output, no secrets.
8. Docs: every number re-derived today; limitations first. (`scripts/claim_audit.py`)
9. Verdict: READY, or NOT READY plus the specific item blocking it.

## Caveats

- What it scores is how the work is structured. It cannot judge correctness and it is not a HackerRank score. Never quote them as predictions.
- Its case-study numbers come from a different edition and dataset; treat them as method examples.
- Where its playbook and this skill differ, `evaluation.md` is canonical.
