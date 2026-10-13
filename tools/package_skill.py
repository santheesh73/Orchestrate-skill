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
  4. With --install DIR, also installs the clean folder at DIR/hackerrank-orchestrate
     (for example DIR = .claude/skills). An existing copy there is replaced only with
     --force, and atomically: the new copy is built and validated beside it first, and
     on any failure the previous copy is left as it was.
  5. With --project DIR, installs into a project's skill folders the same way:
     --for claude gives DIR/.claude/skills (Claude Code), --for agents gives
     DIR/.agents/skills (Codex, Cursor, OpenCode, Antigravity; see docs/INSTALL.md),
     and --for all (the default) gives both. Every target is checked before any is
     written, so an existing copy without --force installs nothing.

Exit 0 on success, 1 when validation fails, 2 on usage errors. Standard library only;
no network. The packaged scripts check a participant's own work; they are not part of
a submission.

Examples:
  python tools/package_skill.py
  python tools/package_skill.py --out /tmp/dist --install ~/.claude/skills --force
  python tools/package_skill.py --project ../my-entry --for all
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
PROJECT_LAYOUTS = {"claude": [".claude/skills"], "agents": [".agents/skills"],
                   "all": [".claude/skills", ".agents/skills"]}
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


def install(staged, target):
    """Install atomically: copy into a sibling temp folder, validate it, then swap it in.

    Failure it prevents: a failed copy (full disk, permissions) leaving no installed skill,
    because the old copy was deleted first. The old copy (a folder, file or symlink, which
    is replaced, not followed) is moved aside, and deleted only after the new one is in
    place; on any failure it is moved back. Raises OSError, or ValueError on validation.
    """
    parent = os.path.dirname(os.path.abspath(target))
    os.makedirs(parent, exist_ok=True)
    work = tempfile.mkdtemp(prefix=".install-", dir=parent)
    old = None
    try:
        new = os.path.join(work, SKILL_NAME)
        shutil.copytree(staged, new)
        errors = []
        validate_skill.check_skill(new, errors)
        if errors:
            raise ValueError(f"the copied skill failed validation: {errors[0]}")
        if os.path.lexists(target):
            old = os.path.join(work, "previous")
            os.rename(target, old)
        try:
            os.rename(new, target)
        except OSError:
            if old:
                os.rename(old, target)
                old = None
            raise
    finally:
        shutil.rmtree(work, ignore_errors=True)  # holds the old copy only after a successful swap


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skill-dir", default=os.path.join(ROOT, SKILL_NAME), help="skill folder to package")
    ap.add_argument("--out", default=os.path.join(ROOT, "dist"), help="output directory for the zip (default dist/)")
    ap.add_argument("--install", metavar="DIR", help="also copy the clean skill to DIR/" + SKILL_NAME)
    ap.add_argument("--project", metavar="DIR", help="also install into the project DIR (see --for)")
    ap.add_argument("--for", dest="layout", choices=sorted(PROJECT_LAYOUTS),
                    help="with --project: .claude/skills, .agents/skills, or both (default all)")
    ap.add_argument("--force", action="store_true", help="replace an existing installed copy")
    args = ap.parse_args(argv)
    if args.layout and not args.project:
        ap.error("--for needs --project DIR")

    if not os.path.isfile(os.path.join(args.skill_dir, "SKILL.md")):
        print(f"error: no SKILL.md in {args.skill_dir}", file=sys.stderr)
        return 2
    targets = [os.path.join(os.path.expanduser(args.install), SKILL_NAME)] if args.install else []
    if args.project:
        project = os.path.expanduser(args.project)
        if not os.path.isdir(project):
            print(f"error: project folder {project} does not exist", file=sys.stderr)
            return 2
        targets += [os.path.join(project, *sub.split("/"), SKILL_NAME)
                    for sub in PROJECT_LAYOUTS[args.layout or "all"]]
    for target in targets:
        if os.path.lexists(target) and not args.force:
            print(f"error: {target} exists; pass --force to replace it; nothing installed", file=sys.stderr)
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
        for target in targets:
            try:
                install(staged, target)
            except (OSError, ValueError) as exc:
                reason = exc.strerror if isinstance(exc, OSError) and exc.strerror else exc
                print(f"error: cannot install to {target}: {reason}; any previous copy is unchanged", file=sys.stderr)
                return 2
            print(f"installed {target}")
    return 0


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):  # a console that cannot encode the data must not crash
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(errors="backslashreplace")
    sys.exit(main())
