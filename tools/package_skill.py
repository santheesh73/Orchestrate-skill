#!/usr/bin/env python3
"""Build an upload-ready zip of the skill, and optionally install a clean copy.

Failure it prevents: a Claude.ai upload rejected because SKILL.md is not at the top of
the skill folder inside the zip, or a skill that ships development files
(__pycache__, *.pyc, tests, fixtures) to every user who installs it.

What it does:
  1. Copies hackerrank-orchestrate/ minus excluded files into a staging folder.
  2. Runs tools/validate_skill.py --standalone on the staged copy; stops on any error.
  3. Writes dist/hackerrank-orchestrate.zip with one top-level folder entry,
     hackerrank-orchestrate/, holding SKILL.md, references/, scripts/ and assets/.
  4. With --install DIR, also copies the clean folder to DIR/hackerrank-orchestrate
     (for example DIR = .claude/skills). An existing copy there is replaced only with
     --force.

Exit 0 on success, 1 when validation fails, 2 on usage errors. Standard library only;
no network. The packaged scripts check a participant's own work; they are not part of
a submission.

Examples:
  python tools/package_skill.py
  python tools/package_skill.py --out /tmp/dist --install ~/.claude/skills --force
"""

import argparse
import fnmatch
import os
import shutil
import sys
import tempfile
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_NAME = "hackerrank-orchestrate"
EXCLUDE_DIRS = {"__pycache__", "tests", "fixtures", ".git", ".pytest_cache"}
EXCLUDE_FILES = ("*.pyc", "*.pyo", ".DS_Store", "Thumbs.db", "*~", "*.swp")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_skill  # noqa: E402


def skill_files(src):
    """Yield (absolute path, path relative to src) for every file that ships."""
    for dirpath, dirnames, filenames in os.walk(src):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDE_DIRS and not d.startswith("."))
        for f in sorted(filenames):
            if any(fnmatch.fnmatch(f, pat) for pat in EXCLUDE_FILES):
                continue
            p = os.path.join(dirpath, f)
            if os.path.islink(p):
                continue
            yield p, os.path.relpath(p, src)


def stage(src, dest):
    for path, rel in skill_files(src):
        target = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy2(path, target)


def write_zip(staged, zip_path):
    os.makedirs(os.path.dirname(os.path.abspath(zip_path)), exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(SKILL_NAME + "/", "")
        for path, rel in skill_files(staged):
            zf.write(path, SKILL_NAME + "/" + rel.replace(os.sep, "/"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skill-dir", default=os.path.join(ROOT, SKILL_NAME), help="skill folder to package")
    ap.add_argument("--out", default=os.path.join(ROOT, "dist"), help="output directory for the zip (default dist/)")
    ap.add_argument("--install", metavar="DIR", help="also copy the clean skill to DIR/" + SKILL_NAME)
    ap.add_argument("--force", action="store_true", help="replace an existing installed copy")
    args = ap.parse_args(argv)

    if not os.path.isfile(os.path.join(args.skill_dir, "SKILL.md")):
        print(f"error: no SKILL.md in {args.skill_dir}", file=sys.stderr)
        return 2
    target = os.path.join(os.path.expanduser(args.install), SKILL_NAME) if args.install else None
    if target and os.path.exists(target) and not args.force:
        print(f"error: {target} exists; pass --force to replace it", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory() as tmp:
        staged = os.path.join(tmp, SKILL_NAME)
        stage(args.skill_dir, staged)
        errors = []
        validate_skill.check_skill(staged, errors)
        for e in errors:
            print(f"ERROR {e}")
        if errors:
            print(f"packaging stopped: {len(errors)} validation errors in the staged copy")
            return 1
        zip_path = os.path.join(args.out, SKILL_NAME + ".zip")
        try:
            write_zip(staged, zip_path)
        except OSError as exc:
            print(f"error: cannot write {zip_path}: {exc.strerror}", file=sys.stderr)
            return 2
        with zipfile.ZipFile(zip_path) as zf:
            n = sum(1 for i in zf.infolist() if not i.is_dir())
        print(f"wrote {zip_path}: {n} files, {os.path.getsize(zip_path)} bytes; staged copy validated")
        if target:
            try:
                if os.path.isdir(target) and not os.path.islink(target):
                    shutil.rmtree(target)
                elif os.path.lexists(target):
                    os.remove(target)
                shutil.copytree(staged, target)
            except OSError as exc:
                print(f"error: cannot install to {target}: {exc.strerror}", file=sys.stderr)
                return 2
            print(f"installed {target}")
    return 0


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):  # a console that cannot encode the data must not crash
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(errors="backslashreplace")
    sys.exit(main())
