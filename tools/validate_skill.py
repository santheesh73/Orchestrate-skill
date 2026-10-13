#!/usr/bin/env python3
"""Validate the skill: structure, content drift, scripts, evals and release metadata.

Failure it prevents: a skill that breaks or drifts silently, for example a reference
to a file that was renamed, a script missing from the SKILL.md table, a description
that grew a date, a second copy of the hard rules, or personal results creeping in.

Run from the repo root:  python tools/validate_skill.py
Check a copied skill folder on its own (as installed under .claude/skills/):
  python tools/validate_skill.py --skill-dir /path/to/.claude/skills/hackerrank-orchestrate --standalone

Exit code 0 when valid, 1 otherwise. Standard library only; no network.
"""

import argparse
import ast
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DATE_RE = re.compile(r"\b(19|20)\d{2}\b|\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\b")
PERSONAL_MARKERS = [re.compile(p, re.I) for p in (r"global\s+#\s*\d", r"\b\d{1,3}(\.\d)?/100\b", r"\brank(ed)?\s+#\s*\d",
                                                    r"\bmy (score|rank)\b")]
MAX_BODY_LINES = 80
MAX_DESC = 900
# Context budgets in characters, set at the size measured for v2.2.0 plus about 10%
# (tools/footprint.py reports the same parts). Raise one only on purpose.
FOOTPRINT_BUDGETS = {"skill_body": 7600, "always_loaded": 8500, "on_demand": 167000}
LINE_LIMITS = {"references/behind-schedule.md": 40, "references/edition-update.md": 40, "references/kit-repo.md": 90}
ARCHETYPE_SECTIONS = ("Architecture that held up", "Guards that fit", "Grounding test", "Where rows are lost")
PROFILE_KEYS = {"name", "entry_regex", "prompt_header", "section_headers", "session_start_title_match",
                "tool_rule", "required_turn_sections", "title_max_length", "secret_scan",
                "provenance", "provenance_source"}
PROVENANCE_LABELS = {"VERIFIED", "INFERRED", "UNKNOWN"}
# Files that live in a participant's starter repo or submission, not in this skill.
EXTERNAL_FILES = {"problem_statement.md", "usage_report.md", "evalutation_criteria.md", "decisions.md", "changes.md"}
TEXT_EXTS = (".md", ".py", ".json", ".yml", ".yaml", ".txt", ".csv")


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


def read(path):
    """Lenient read: check_files reports invalid UTF-8 once, so later checks must not crash on it."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


TEXT_EXTS = (".md", ".py", ".json", ".txt", ".csv", ".yml", ".yaml")


def check_files(skill_dir, errors):
    """Report broken symlinks and text files that are not UTF-8; both break an installed skill."""
    for dirpath, dirnames, files in os.walk(skill_dir):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for fn in files:
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, skill_dir)
            if not os.path.exists(p):
                errors.append(f"{rel} is a broken symlink")
            elif fn.endswith(TEXT_EXTS):
                try:
                    with open(p, encoding="utf-8") as fh:
                        fh.read()
                except UnicodeDecodeError:
                    errors.append(f"{rel} is not valid UTF-8")


def on_demand_chars(skill_dir):
    total = 0
    for dirpath, dirnames, filenames in os.walk(skill_dir):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for f in filenames:
            p = os.path.join(dirpath, f)
            if (f.endswith((".pyc", ".pyo")) or os.path.relpath(p, skill_dir) == "SKILL.md"
                    or not os.path.isfile(p)):
                continue
            with open(p, encoding="utf-8", errors="replace") as fh:
                total += len(fh.read())
    return total


def check_skill(skill_dir, errors):
    skill_md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.exists(skill_md):
        errors.append(f"{skill_md} not found")
        return None
    check_files(skill_dir, errors)
    text = read(skill_md)
    fm, body = frontmatter(text)
    if fm is None:
        errors.append("SKILL.md has no YAML frontmatter")
        fm = {}
    name, desc = fm.get("name", ""), fm.get("description", "")
    if not NAME_RE.match(name) or len(name) > 64:
        errors.append(f"name {name!r} must be kebab-case, at most 64 characters")
    if name != os.path.basename(os.path.normpath(skill_dir)):
        errors.append(f"name {name!r} must match the folder name {os.path.basename(os.path.normpath(skill_dir))!r}")
    if not desc:
        errors.append("description is empty")
    if len(desc) > MAX_DESC:
        errors.append(f"description is {len(desc)} characters; the limit here is {MAX_DESC}")
    if "<" in desc or ">" in desc:
        errors.append("description must not contain angle brackets")
    if DATE_RE.search(desc):
        errors.append(f"description contains a date ({DATE_RE.search(desc).group(0)!r}); keep the trigger evergreen")
    if not re.search(r"\bdo not use for\b", desc, re.I):
        errors.append("description needs an explicit 'Do not use for ...' clause")
    extra = set(fm) - {"name", "description", "license", "allowed-tools", "metadata"}
    if extra:
        errors.append(f"unexpected frontmatter keys: {sorted(extra)}")
    body_lines = len(body.strip("\n").splitlines())
    if body_lines >= MAX_BODY_LINES:
        errors.append(f"SKILL.md body is {body_lines} lines; keep it under {MAX_BODY_LINES}")
    sizes = {"skill_body": len(body), "always_loaded": len(desc) + len(body), "on_demand": on_demand_chars(skill_dir)}
    for part, limit in sorted(FOOTPRINT_BUDGETS.items()):
        if sizes[part] > limit:
            errors.append(f"footprint: {part} is {sizes[part]} characters, over its budget of {limit} "
                          "(see tools/footprint.py)")

    # Hard rules: one numbered, contiguous list in SKILL.md.
    m = re.search(r"^## Hard rules.*?$(.*?)(?=^## )", body, re.S | re.M)
    if not m:
        errors.append("SKILL.md has no '## Hard rules' section")
    else:
        nums = [int(n) for n in re.findall(r"^(\d+)\.\s", m.group(1), re.M)]
        if not nums or nums != list(range(1, len(nums) + 1)):
            errors.append(f"hard rules must be numbered 1..N contiguously, found {nums}")
        for i, rule in enumerate(re.findall(r"^\d+\.\s+\*\*(.+?)\*\*", m.group(1), re.M), 1):
            phrase = rule.strip().rstrip(".")
            for dirpath, _, files in os.walk(skill_dir):
                for fn in files:
                    p = os.path.join(dirpath, fn)
                    if fn.endswith(".md") and p != skill_md and os.path.isfile(p) and phrase in read(p):
                        errors.append(f"hard rule {i} is restated verbatim in {os.path.relpath(p, skill_dir)}; link instead")

    # Every referenced path exists inside the skill folder.
    for dirpath, _, files in os.walk(skill_dir):
        for fn in files:
            path = os.path.join(dirpath, fn)
            if not fn.endswith(".md") or not os.path.isfile(path):
                continue
            rel = os.path.relpath(path, skill_dir)
            content = read(path)
            for ref in sorted(set(re.findall(r"`?((?:references|scripts|assets)/[A-Za-z0-9_./\-]+)`?", content))):
                ref = ref.rstrip(".")
                if not os.path.exists(os.path.join(skill_dir, ref)):
                    errors.append(f"{rel}: references missing path {ref}")
            if os.path.basename(dirpath) in ("references", "archetypes"):
                for ref in sorted(set(re.findall(r"`([a-z0-9_\-]+\.md)`", content)) - EXTERNAL_FILES):
                    candidates = [os.path.join(dirpath, ref), os.path.join(skill_dir, "references", ref),
                                  os.path.join(skill_dir, "references", "archetypes", ref),
                                  os.path.join(skill_dir, "assets", ref), os.path.join(skill_dir, ref)]
                    if not any(os.path.exists(c) for c in candidates):
                        errors.append(f"{rel}: references missing file {ref}")
            n = len(content.splitlines())
            if rel.startswith("references") and n > 100 and "## Contents" not in content:
                errors.append(f"{rel} is {n} lines; files over 100 lines need a '## Contents' list")
            limit = LINE_LIMITS.get(rel.replace(os.sep, "/"))
            if limit and n > limit:
                errors.append(f"{rel} is {n} lines; the limit is {limit}")

    if os.path.exists(os.path.join(skill_dir, "README.md")):
        errors.append("the skill folder must not contain README.md; keep it at the repo root")

    arch = os.path.join(skill_dir, "references", "archetypes")
    for fn in sorted(os.listdir(arch)) if os.path.isdir(arch) else []:
        if fn.endswith(".md") and fn != "index.md":
            content = read(os.path.join(arch, fn))
            for sec in ARCHETYPE_SECTIONS:
                if not re.search(r"^## " + re.escape(sec), content, re.M):
                    errors.append(f"archetypes/{fn} lacks a '## {sec}' section")

    editions = os.path.join(skill_dir, "assets", "editions")
    for fn in sorted(os.listdir(editions)) if os.path.isdir(editions) else []:
        if fn.endswith(".json"):
            try:
                prof = json.loads(read(os.path.join(editions, fn)))
                missing = PROFILE_KEYS - set(prof)
                if missing:
                    errors.append(f"assets/editions/{fn} lacks keys {sorted(missing)}")
                if "provenance" in prof and prof["provenance"] not in PROVENANCE_LABELS:
                    errors.append(f"assets/editions/{fn}: provenance must be one of {sorted(PROVENANCE_LABELS)}")
                if "provenance_source" in prof and not str(prof["provenance_source"]).strip():
                    errors.append(f"assets/editions/{fn}: provenance_source is empty")
                re.compile(prof.get("entry_regex", ""))
            except (ValueError, re.error) as exc:
                errors.append(f"assets/editions/{fn}: {exc}")

    # Scripts: listed in SKILL.md and vice versa; docstring naming the failure; --help works.
    scripts_dir = os.path.join(skill_dir, "scripts")
    on_disk = sorted(f for f in os.listdir(scripts_dir) if f.endswith(".py")) if os.path.isdir(scripts_dir) else []
    listed = sorted(set(re.findall(r"`scripts/([a-z_]+\.py)", body)))
    for f in sorted(set(on_disk) - set(listed)):
        errors.append(f"scripts/{f} is not listed in the SKILL.md scripts table")
    for f in sorted(set(listed) - set(on_disk)):
        errors.append(f"SKILL.md lists scripts/{f}, which does not exist")
    for f in on_disk:
        p = os.path.join(scripts_dir, f)
        check_python(p, f"scripts/{f}", errors, require_failure_line=True)
        proc = subprocess.run([sys.executable, p, "--help"], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=60)
        if proc.returncode != 0 or b"usage" not in proc.stdout.lower():
            errors.append(f"scripts/{f} --help failed (exit {proc.returncode})")
    return desc


def check_python(path, label, errors, require_failure_line=False):
    src = read(path)
    try:
        tree = ast.parse(src, feature_version=(3, 9))
    except SyntaxError as exc:
        errors.append(f"{label} does not parse as Python 3.9: {exc.msg} (line {exc.lineno})")
        return
    doc = ast.get_docstring(tree) or ""
    if not doc:
        errors.append(f"{label} has no module docstring")
    elif require_failure_line and "Failure it prevents" not in doc:
        errors.append(f"{label} docstring must name the failure it prevents ('Failure it prevents: ...')")


def hard_rule_titles(skill_md):
    _, body = frontmatter(read(skill_md))
    m = re.search(r"^## Hard rules.*?$(.*?)(?=^## )", body, re.S | re.M)
    return [r.strip().rstrip(".") for r in re.findall(r"^\d+\.\s+\*\*(.+?)\*\*", m.group(1), re.M)] if m else []


def check_docs_restate_no_rules(root, errors):
    """Hard rules have one copy: the README and docs/ link to SKILL.md instead of restating them."""
    docs = [os.path.join(root, "README.md")]
    docs_dir = os.path.join(root, "docs")
    docs += sorted(os.path.join(docs_dir, f) for f in os.listdir(docs_dir) if f.endswith(".md")) if os.path.isdir(docs_dir) else []
    titles = hard_rule_titles(os.path.join(root, "hackerrank-orchestrate", "SKILL.md"))
    for path in docs:
        if os.path.exists(path):
            text = read(path)
            for i, phrase in enumerate(titles, 1):
                if phrase in text:
                    errors.append(f"hard rule {i} is restated verbatim in {os.path.relpath(path, root)}; link instead")


def check_repo(errors):
    check_docs_restate_no_rules(ROOT, errors)
    evals_path = os.path.join(ROOT, "evals", "triggers.json")
    try:
        evals = json.loads(read(evals_path))
        if not isinstance(evals, list):
            raise ValueError("top level must be a list")
        bad = [i for i, e in enumerate(evals)
               if not isinstance(e.get("query"), str) or not isinstance(e.get("should_trigger"), bool)]
        if bad:
            errors.append(f"evals/triggers.json entries need query (str) and should_trigger (bool): {bad}")
        pos = sum(1 for e in evals if e.get("should_trigger") is True)
        neg = sum(1 for e in evals if e.get("should_trigger") is False)
        if pos < 20 or neg < 20:
            errors.append(f"evals/triggers.json needs at least 20 positive and 20 negative cases, has {pos}/{neg}")
        queries = [e.get("query", "").strip().lower() for e in evals]
        dupes = sorted({q for q in queries if queries.count(q) > 1})
        if dupes:
            errors.append(f"evals/triggers.json has duplicate queries: {dupes[:3]}")
    except (OSError, ValueError) as exc:
        errors.append(f"evals/triggers.json: {exc}")

    for sub in ("tools", "tests"):
        d = os.path.join(ROOT, sub)
        for dirpath, _, files in os.walk(d):
            for fn in files:
                if fn.endswith(".py") and "fixtures" not in dirpath:
                    check_python(os.path.join(dirpath, fn), os.path.relpath(os.path.join(dirpath, fn), ROOT), errors)

    version_file = os.path.join(ROOT, "VERSION")
    if not os.path.exists(version_file):
        errors.append("VERSION file missing")
    else:
        version = read(version_file).strip()
        if not re.search(r"^## " + re.escape(version) + r"\b", read(os.path.join(ROOT, "CHANGELOG.md")), re.M):
            errors.append(f"CHANGELOG.md has no '## {version}' entry for the VERSION file")

    me = os.path.abspath(__file__)
    for dirpath, dirnames, files in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__")]
        for fn in files:
            p = os.path.join(dirpath, fn)
            if not fn.endswith(TEXT_EXTS) or os.path.abspath(p) == me:
                continue
            try:
                content = read(p)
            except UnicodeDecodeError:
                continue
            for rx in PERSONAL_MARKERS:
                m = rx.search(content)
                if m:
                    errors.append(f"{os.path.relpath(p, ROOT)}: possible personal-result marker {m.group(0)!r}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skill-dir", default=os.path.join(ROOT, "hackerrank-orchestrate"))
    ap.add_argument("--standalone", action="store_true", help="check only the skill folder (no repo-level checks)")
    args = ap.parse_args(argv)
    errors = []
    desc = check_skill(args.skill_dir, errors)
    if not args.standalone:
        check_repo(errors)
    for e in errors:
        print(f"ERROR {e}")
    print(f"description: {len(desc or '')} characters; {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
