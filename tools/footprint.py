#!/usr/bin/env python3
"""Report the skill's context footprint: what is always loaded and what loads on demand.

Failure it prevents: the always-loaded part of the skill (the description, which sits in
every conversation, and the SKILL.md body, which loads whenever the skill triggers)
growing a little with every edit until it crowds the context, with nobody deciding it.

Token counts are ESTIMATED as characters / 4; they are not a tokenizer's output.
Budgets live in tools/validate_skill.py (FOOTPRINT_BUDGETS) at the measured size plus
about 10%; raising one is a deliberate edit that shows up in review.

Exit 0 when every part is within budget, 1 when one is over, 2 on usage errors.
Standard library only; no network.

Example:
  python tools/footprint.py            # table of every file, then the totals
  python tools/footprint.py --summary  # totals only
"""

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_skill  # noqa: E402

SKIP_DIRS = {"__pycache__"}


def est_tokens(chars):
    return (chars + 3) // 4


def measure(skill_dir):
    """Return (parts, files): character counts per part, and (relpath, bytes, chars) per file."""
    skill_md = os.path.join(skill_dir, "SKILL.md")
    fields, body = validate_skill.frontmatter(validate_skill.read(skill_md))
    if fields is None:
        raise ValueError(f"{skill_md} has no frontmatter")
    parts = {"description": len(fields.get("description", "")), "skill_body": len(body)}
    files = []
    for dirpath, dirnames, filenames in os.walk(skill_dir):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for f in sorted(filenames):
            if f.endswith((".pyc", ".pyo")):
                continue
            p = os.path.join(dirpath, f)
            rel = os.path.relpath(p, skill_dir).replace(os.sep, "/")
            with open(p, encoding="utf-8", errors="replace") as fh:
                chars = len(fh.read())
            files.append((rel, os.path.getsize(p), chars))
    parts["on_demand"] = validate_skill.on_demand_chars(skill_dir)
    parts["always_loaded"] = parts["description"] + parts["skill_body"]
    return parts, files


def over_budget(parts, budgets=None):
    if budgets is None:
        budgets = dict(validate_skill.FOOTPRINT_BUDGETS, description=validate_skill.MAX_DESC)
    return [(k, parts[k], limit) for k, limit in sorted(budgets.items()) if parts.get(k, 0) > limit]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skill-dir", default=os.path.join(ROOT, "hackerrank-orchestrate"))
    ap.add_argument("--summary", action="store_true", help="print totals only")
    args = ap.parse_args(argv)
    if not os.path.isfile(os.path.join(args.skill_dir, "SKILL.md")):
        print(f"error: no SKILL.md in {args.skill_dir}", file=sys.stderr)
        return 2
    try:
        parts, files = measure(args.skill_dir)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if not args.summary:
        print(f"{'file':<48} {'bytes':>8} {'est. tokens':>12}")
        for rel, size, chars in files:
            print(f"{rel:<48} {size:>8} {est_tokens(chars):>12}")
        print()
    budgets = dict(validate_skill.FOOTPRINT_BUDGETS, description=validate_skill.MAX_DESC)
    print("part             chars   est. tokens (ESTIMATED, chars/4)   budget (chars)")
    for k in ("description", "skill_body", "always_loaded", "on_demand"):
        limit = budgets.get(k)
        print(f"{k:<14} {parts[k]:>8}   {est_tokens(parts[k]):>8}                          {limit if limit else '-'}")
    over = over_budget(parts)
    for k, v, limit in over:
        print(f"OVER BUDGET {k}: {v} chars > {limit}; trim it, or raise FOOTPRINT_BUDGETS in validate_skill.py on purpose")
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
