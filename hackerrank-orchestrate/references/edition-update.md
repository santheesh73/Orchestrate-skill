# After each edition

Failure it prevents: the skill drifting out of date after an edition (stale contract notes, a log format the checker rejects, a new problem shape with no page).

Run this once the edition closes and its starter repo, problem and any organizer write-up are public. Keep personal results out of the skill; put them in project memory.

1. **Starter contract diff.** `python scripts/contract_extract.py --diff OLD_STARTER NEW_STARTER`, then read both `AGENTS.md` files in full. Add every new MUST to `starter-contract.md` under "known changes", with the edition name.
2. **Log profile.** If the log format changed, copy `assets/editions/template.json` to a new file named after the edition in the same folder, fill it from the new `AGENTS.md`, set `provenance` (VERIFIED only when every field is stated in the real starter) and `provenance_source`, add a fixture log and a test, and run `check_log.py --list-profiles`. Change the default profile only after the next edition's starter confirms the format.
3. **Archetype.** If the problem shape is new, add a page under `archetypes/` with the four required parts (architecture, guards, grounding test, where rows are lost) and a row in `archetypes/index.md`. If it fits an existing page, add only what is new.
4. **Rubric.** If the organizer publishes new weights, caps or leaderboard analysis, update `rubric.md` and label each figure VERIFIED, INFERRED or UNKNOWN with its source.
5. **Starter paths in examples.** Check that column names and paths used as examples in `output-csv.md` and `prompt-templates.md` still say which edition they come from.
6. **Trigger evals.** Add at least two should-trigger prompts phrased the way the new edition talks, and one near-miss negative. Run `tools/run_trigger_evals.py --offline`, and `--live` if a key is available.
7. **Validate and release.** `python tools/validate_skill.py`, `python -W error -m unittest discover -s tests`, bump the version, add a CHANGELOG entry.
