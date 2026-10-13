# Simulation and planning

Shape: reconstruct state from structured records, simulate forward over time, and pick a safe plan under constraints and a stated tie-break order. Source: the September 2026 starter ("Buy or Wait?") and lessons from mid-to-top finishers in that edition.

## Architecture that held up

- **Deterministic core does all the arithmetic:** state reconstruction, currency normalization (exact dated rate match, no guessing), the forward simulation, the safe amount (for example by binary search over the simulation), earliest feasible dates, plan enumeration, the tie-break, and strict format enforcement.
- **The model does three limited things:** extract facts from messages and images that change records (cancel, delay, confirm), write the explanation, and stay robust to untrusted content. It never touches a final number.
- **Enumerate plan candidates in the base design.** Full, partial, each supplied installment option, waiting, and permitted spending changes, each simulated and checked against the constraints. A design that only tried the full payment missed every row that needed a plan.
- **Encode the conflict-resolution order and tie-break order exactly as stated,** as ordered code. Cover the tie-break with a unit test in which each criterion points a different way.

## Guards that fit

- **Decide grouping keys and the statistic before writing a recurrence detector.** Grouping by (category, description, direction) made categories with many rotating vendors (groceries, dining, transport) never clear the recurrence threshold, so they projected as zero spend. The fix was deciding upfront which categories are fixed-vendor (group by category and description) and which are volatile-but-real (group by category alone), with a robust statistic and a bounded cadence for the volatile ones. Patching after the fact overshot repeatedly.
- **Do not count unsettled or non-cash credits** (pending refunds, bonuses, commissions, unrealized gains) until they settle, as the contract says. Check that variable income is not treated as fixed salary.
- **Never branch on whether a model-written field is empty** (hard rule 6). In one project, `if args.get("uncertainty")` blocked a right answer because the model had filled the field with the words "None - confirmed salary".
- **Same-date ordering** (debits versus credits on one day) is a decision the judge asks about. Pick it from the contract or the conservative reading, document it beside the code, and know it cold.

## Grounding test

Remove a message that amends an event (a cancellation or delay) and rerun that row; the plan must change. Remove the user's minimum-balance constraint in a test fixture; plans that were rejected for it must become feasible.

## Where rows are lost

- Spend projection: categories that project to zero, or a statistic chosen to match samples rather than the domain.
- Plan enumeration gaps: rows that needed a partial plan or spending change when the code only tried full payment.
- Boundary dates (inclusive versus exclusive forecast ends, off-by-one on the earliest date).
- A systematic 5% to 25% miss in the same direction across many rows usually means one simulation bug, not many independent errors.
