#!/usr/bin/env python3
"""Validate the skill folder: frontmatter, referenced files, script syntax, trigger evals.

Run from the repo root: python tools/validate_skill.py
Exit code 0 when valid, 1 otherwise. Standard library only.
"""

import json
import os
import py_compile
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_DIR = os.path.join(ROOT, "hackerrank-orchestrate")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
TRIGGERS = os.path.join(ROOT, "evals", "triggers.json")
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DATE_RE = re.compile(r"\b(19|20)\d{2}\b|\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\b")


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, text
    fields = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            fields[k.strip()] = v.strip()
    return fields, text[m.end():]


def main():
    errors = []
    with open(SKILL_MD, encoding="utf-8") as fh:
        text = fh.read()
    fm, body = frontmatter(text)
    if fm is None:
        errors.append("SKILL.md has no YAML frontmatter")
        fm = {}
    name, desc = fm.get("name", ""), fm.get("description", "")
    if not NAME_RE.match(name) or len(name) > 64:
        errors.append(f"name {name!r} must be kebab-case, at most 64 characters")
    if name != os.path.basename(SKILL_DIR):
        errors.append(f"name {name!r} must match the folder name {os.path.basename(SKILL_DIR)!r}")
    if not desc:
        errors.append("description is empty")
    if len(desc) > 1024:
        errors.append(f"description is {len(desc)} characters; the limit is 1024")
    if "<" in desc or ">" in desc:
        errors.append("description must not contain angle brackets")
    if DATE_RE.search(desc):
        errors.append(f"description contains a date ({DATE_RE.search(desc).group(0)!r}); keep the trigger evergreen")
    extra = set(fm) - {"name", "description", "license", "allowed-tools", "metadata"}
    if extra:
        errors.append(f"unexpected frontmatter keys: {sorted(extra)}")
    if len(body.splitlines()) > 500:
        errors.append("SKILL.md body is over 500 lines; move detail into references/")

    # Every references/, scripts/ or assets/ path named anywhere in the skill must exist.
    for dirpath, _, files in os.walk(SKILL_DIR):
        for fn in files:
            if not fn.endswith(".md"):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, ROOT)
            with open(path, encoding="utf-8") as fh:
                content = fh.read()
            for ref in sorted(set(re.findall(r"`?((?:references|scripts|assets)/[A-Za-z0-9_./\-]+)`?", content))):
                ref = ref.rstrip(".")
                if not os.path.exists(os.path.join(SKILL_DIR, ref)):
                    errors.append(f"{rel}: references missing path {ref}")
            # Bare sibling links inside references/ (e.g. `evaluation.md`).
            if os.path.basename(dirpath) in ("references", "archetypes"):
                for ref in sorted(set(re.findall(r"`([a-z0-9\-]+\.md)`", content))):
                    candidates = [os.path.join(dirpath, ref), os.path.join(SKILL_DIR, "references", ref),
                                  os.path.join(SKILL_DIR, "references", "archetypes", ref),
                                  os.path.join(SKILL_DIR, "assets", ref), os.path.join(SKILL_DIR, ref)]
                    if not any(os.path.exists(c) for c in candidates):
                        errors.append(f"{rel}: references missing file {ref}")

    if os.path.exists(os.path.join(SKILL_DIR, "README.md")):
        errors.append("the skill folder must not contain README.md; keep it at the repo root")

    scripts = os.path.join(SKILL_DIR, "scripts")
    for fn in sorted(os.listdir(scripts)):
        if fn.endswith(".py"):
            try:
                py_compile.compile(os.path.join(scripts, fn), doraise=True)
            except py_compile.PyCompileError as exc:
                errors.append(f"scripts/{fn} does not compile: {exc.msg}")

    try:
        with open(TRIGGERS, encoding="utf-8") as fh:
            evals = json.load(fh)
        if not isinstance(evals, list):
            raise ValueError("top level must be a list")
        pos = sum(1 for e in evals if e.get("should_trigger") is True)
        neg = sum(1 for e in evals if e.get("should_trigger") is False)
        bad = [i for i, e in enumerate(evals) if not isinstance(e.get("query"), str) or not isinstance(e.get("should_trigger"), bool)]
        if bad:
            errors.append(f"evals/triggers.json entries need query (str) and should_trigger (bool): {bad}")
        if pos < 10 or neg < 8:
            errors.append(f"evals/triggers.json needs at least 10 positive and 8 negative cases, has {pos}/{neg}")
    except (OSError, ValueError) as exc:
        errors.append(f"evals/triggers.json: {exc}")

    for e in errors:
        print(f"ERROR {e}")
    print(f"description: {len(desc)} characters; {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
