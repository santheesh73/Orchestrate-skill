# Optional: the community toolkit

`hackerrank-orchestrate-skills` is a community repository (not affiliated with HackerRank) with auto-triggering skills and a zero-dependency Python CLI that audits a submission repo. This skill does not require it; `self-score.md` Path A is a complete gate without it.

This digest was written from the toolkit's state as of its "Phase 2: experiment tracker + live score delta loop" commit. Commands may have changed since; trust `--help` over this page.

## Install (if the user has it)

```bash
cd hackerrank-orchestrate-skills
pip install -e .
python -m orchestrate_kit memory seed
python -m orchestrate_kit selftest
```

`python -m orchestrate_kit` always works; the plain `orchestrate` command needs the install directory on PATH. Do not copy its skills into `.claude/skills/` alongside this one unless the user wants both; overlapping triggers compete.

## Commands worth knowing

| Command | Use |
|---|---|
| `orchestrate evaluate <repo>` | Shippable? Exit 2 on any blocker |
| `orchestrate release <repo>` | Final gate with manual items; the last is the authorship attestation |
| `orchestrate mentor "<proposal>"` | Pre-mortem before building; prints UNKNOWN rather than guessing a gain |
| `orchestrate memory why-not "<idea>"` | Queryable rejection log; avoids re-building a known loser |
| `orchestrate experiment start/finish` | Tool form of the change-record loop: baseline, change, measure, accept or reject |
| `orchestrate interview --persona … --difficulty …` | Judge simulator; scores answer shape, not truth |
| `orchestrate transcript analyze <file>` | Lints a transcript against the published dimensions |

Every finding carries a confidence label (measured / observed / inferred / unknown); a skipped audit is UNKNOWN, never a pass.

## Its method in one line

Measure before shipping, measure blast radius, prove the counterfactual, attack your own measurement before trusting it. Its 20-rule playbook overlaps heavily with `evaluation.md` and `loop-patterns.md`; where they differ, this skill's `evaluation.md` resolution table is canonical.

## Caveats

- Its scores measure the shape of an answer or process, not correctness, and not a real HackerRank score. Never quote them as predictions.
- Its case-study numbers come from a different edition and dataset; treat them as method examples, not benchmarks.
