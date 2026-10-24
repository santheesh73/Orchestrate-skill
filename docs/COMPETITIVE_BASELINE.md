# Competitive baseline

## Before implementation

Date: 2026-10-24; Windows, Python 3.14.3. Baseline source:
`b77723d7e17fb95db96d654cd99530d1f72b0228`. Command:
`python -W error -m unittest discover -s tests -v`.
Fresh result: **219 tests, 295.106 seconds, OK (two platform-specific skips)**,
exit zero. This was executed before any implementation change. Historical
results were not substituted for this run.

Competitor:
`https://github.com/NITISH-R-G/hackerrank-orchestrate-skills`, revision
`ccb175f8717f67fd084c57d853076f0b95636980`, public HEAD verified unchanged.
`python -m orchestrate_kit selftest` exited zero: baseline clean, ten of ten
injected defects caught, three of three benign cases quiet. This tests the
competitor on its own controls and cannot establish comparative superiority.

## Independent comparison

The baseline and plan were committed as `83b0f724d3aa2919198fab4061036863a13bf15c`
before implementation. The original checker files remain byte-for-byte unchanged.
The shared runner was then executed against both reviewed checkouts. Results:
[preserved scanner](../benchmarks/comparison/baseline-windows.json) and
[new optional audit](../benchmarks/comparison/improved-windows.json).

Each JSON records the actual Git HEAD and working-tree dirtiness at execution,
plus hashes of the exercised checker sources, fixture suite, worker and runner.
The new audit was measured while its code was uncommitted: use those file hashes
and the implementation commit, rather than assuming Git HEAD alone identifies
that working tree. The packaging and original scanner hashes identify unchanged
baseline sources. Reports are observations, not signed attestations.

### Equal-denominator results

The common-interface view excludes mandatory-usage and environment-sidecar
policies for **both** engines, because the competitor's packager has no knobs for
those requirements. The three scenarios are N/A for its policy support. Actual
acceptance/refusal observations remain visible in the raw cases. Unknown process
outcomes would also be excluded, with an explicit count; none occurred here.

| Check on shared synthetic cases | This repo, preserved scanner | This repo, optional decision_ids | Competitor |
|---|---|---|---|
| Packaging defects blocked | 12/12 | 12/12 | 10/12 |
| Healthy packages accepted | 4/4 | 4/4 | 4/4 |
| Literal-ID decision defects detected | 3/3 | 3/3 | 2/3 |
| Benign source cases kept quiet | 4/5 | 5/5 | 4/5 |
| Existing skill folder conflict preserves user content | PASS | PASS | FAIL |
| File discovery | Five skill files | Five skill files | Eight skill files |
| Live activation in coding agents | UNKNOWN | UNKNOWN | UNKNOWN |

The two shared packaging misses were an extra CSV field and header-only data.
The competitor accepted the three additional unsupported-policy scenarios
(missing/empty mandatory usage report and an environment sidecar); these are
feature gaps, not included in its common-interface error rate. Our configured
packager blocked all fifteen defective scenarios and accepted all four healthy
ones. The existing-folder conflict test used mapped canonical names and a
temporary destination, not a participant's real home directory.

The broad original corpus scanner flags the benign fixture assignment. It is an
investigation heuristic, so this is a false positive relative to this benchmark's
narrow decision-ID policy, not proof that the old tool is defective. The new
opt-in AST audit avoids it while still catching the three injected decisions.
The competitor flags the unseen probe ID and misses the other-domain input ID.
These observations motivated a data-driven policy; no original checker was
removed, modified or silently replaced.

In the improved run, shared packaging checks took about 2.12 seconds here and
1.52 seconds for the competitor; leakage checks took about 0.86 and 1.01 seconds.
These are single-run totals including interpreter startup and filesystem effects,
with other local validation running. They do not support a performance ranking.

### Limits and follow-up

There are only nineteen packaging scenarios and eight leakage scenarios. They
cover documented invariants and known failure classes, not random or blinded
samples. No confidence interval, real-world FP/FN rate, hidden-label accuracy,
official score or overall superiority follows from them. A more representative
multi-edition corpus and independent holdout are still needed.

Instruction text in input tests whether a checker treats it as data; it does not
test an agent's resistance to prompt injection. Detection is static and literal:
dynamic ID construction/dataflow and non-Python source remain unsupported by the
new audit and return UNKNOWN where detectable. Dry-run, backups, idempotency and
uninstallation are covered by our existing tests, not independently compared in
this runner. The competitor's other evaluator, memory and interview capabilities
are not ranked by its packaging-script results. Its own selftest remains passing.

See [the plan](V2_IMPLEMENTATION_PLAN.md) for later sprints. This increment
implements Sprint 1 plus the first measured audit improvement; it does not claim
completion of all six sprints.
