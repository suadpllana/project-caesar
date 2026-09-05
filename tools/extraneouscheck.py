#!/usr/bin/env python3
r"""Does the bundle ship anything nothing in the bundle uses?

`permit-strand-relay` cleared the structural check, the AI screen, the similarity
screen and reference verification, and failed the quality review on the single
criterion `no extraneous files`. Three files, and each is a class rather than an
accident:

    authoring/decisions.py   its only reader is tools/onelinecheck.py, which does
                             not ship, so from inside the archive it is an orphan
    authoring/gen.py         byte-identical to tests/gen.py
    authoring/trial.py       CA = "/root/.ccr/ca-bundle.crt", an author-local path

The reviewer accepted the rest of `authoring/` - ground-truth derivation, variant
generation, cheat generation, the probes - as reviewer tooling that earns its
place. So the rule is not "authoring/ is cruft". It is narrower and mechanical:

    a shipped file must be reachable from inside the bundle, must not be a copy
    of another shipped file, and must not name a path that exists only on the
    machine that wrote it.

WHAT IT LOOKS FOR

  ORPHAN     a module under authoring/ that nothing in the bundle imports and
             that cannot be run either - no __main__ guard and no module-level
             work. A runnable gate is fine however lonely it is; a library whose
             only caller lives in tools/ is not.
  DUPLICATE  a file under authoring/ with the same bytes as one that ships
             elsewhere. Every other identical pair in a bundle is load-bearing:
             tests/pristine mirrors environment/app_src by definition, and a
             variant is the reference with one decision changed.
  HOSTPATH   an absolute path from the authoring machine that the next machine
             cannot override. /root, /home/<user>, /Users/<user>, C:\Users and
             C:\Program Files, unless an environment variable or a PATH lookup
             sits beside it - a probe among candidates is not a hardcode, and
             is_file() alone is not an override, because the rejected file was
             guarded that way and still had one source.
  SCRATCH    editor backups and empty files. Caches, bytecode, logs and STATE.md
             are excluded here because package.py drops them; measuring the tree
             instead of the archive reports them on bundles that shipped clean.

VALIDATED IN BOTH DIRECTIONS, 2026-09-05. It names exactly the reviewer's three
findings on a reconstruction of the rejected bundle and nothing else, and it is
clean on every bundle here that has cleared a quality review: guard-mark-unwind
and typeahead-query-controller (nine gates), share-register-screen (the whole
pipeline), alias-settle-report, delta-view-retraction and the rest. It also
reports three bundles that are latent for this rejection if they go back as they
stand - note-carry-forward, grant-spread-order and segment-merge-horizon.

Usage:
    python3 tools/extraneouscheck.py <slug> [<slug> ...]
    python3 tools/extraneouscheck.py --all
"""

from __future__ import annotations

import ast
import hashlib
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASKS = ROOT / "tasks"

TEXT = {".py", ".sh", ".md", ".toml", ".json", ".txt", ".cfg", ".ini", ""}

HOST = (
    (re.compile(r"/root/[A-Za-z0-9._-]"), "/root/..."),
    (re.compile(r"/home/[A-Za-z0-9._-]+/"), "/home/<user>/..."),
    (re.compile(r"/Users/[A-Za-z0-9._-]+/"), "/Users/<user>/..."),
    (re.compile(r"[A-Za-z]:\\?Users\\?"), r"C:\Users\..."),
    (re.compile(r"[A-Za-z]:[\\/]Program Files"), r"C:\Program Files..."),
)

# What package.py drops on its way to the archive. Measuring the working tree
# instead would report STATE.md and every .pyc on bundles that shipped clean.
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".ruff_cache",
             "logs", "runs", ".harbor", "jobs", "job", "results", "trials"}
SKIP_NAMES = {"STATE.md", ".DS_Store", "Thumbs.db", ".gitignore", ".gitattributes"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".zip", ".log"}

SCRATCH = (
    ("editor backup", lambda p: p.suffix in (".orig", ".bak", ".rej", ".swp")),
    ("empty file", lambda p: p.name != "__init__.py" and p.stat().st_size == 0),
)


def shipped(task: Path):
    """Every file package.py would put in the archive."""
    for p in sorted(task.rglob("*")):
        if not p.is_file():
            continue
        if set(p.relative_to(task).parts[:-1]) & SKIP_DIRS:
            continue
        if p.name in SKIP_NAMES or p.suffix in SKIP_SUFFIXES:
            continue
        yield p


SETUP = ("sys.path.insert", "sys.path.append", "warnings.filterwarnings")


def runnable(src: str) -> bool:
    """Does this module do anything when you run it?

    Import lines, constants and the sys.path preamble every authoring script
    carries are setup, not work: a module that stops there only exists to be
    imported, so if nothing imports it, nothing reaches it at all.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return True
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef,
                             ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue                     # a docstring is not work
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            if any(ast.unparse(node.value.func).endswith(s.split(".")[-1])
                   and ast.unparse(node.value.func).startswith(s.split(".")[0])
                   for s in SETUP):
                continue
        if isinstance(node, ast.If) and "__main__" in ast.unparse(node.test):
            return True
        return True                      # a bare call, loop or print at import time
    return False


def orphans(task: Path, files):
    """Modules under authoring/ nothing in the bundle can reach."""
    home = task / "authoring"
    mods = {p.stem: p for p in home.glob("*.py")}
    if not mods:
        return []
    bodies = {}
    for p in files:
        if p.suffix in TEXT or p.suffix == "":
            try:
                bodies[p] = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                pass
    out = []
    for name, path in sorted(mods.items()):
        src = bodies.get(path, "")
        if runnable(src):
            continue
        pat = re.compile(r"(?:^|[^\w.])(?:import\s+%s\b|from\s+%s\s|%s\.py\b|[\"']%s[\"'])"
                         % (name, name, name, name), re.M)
        if any(other is not path and pat.search(body) for other, body in bodies.items()):
            continue
        out.append("ORPHAN     authoring/%s.py is a library with no reader in the bundle "
                   "and no way to run it" % name)
    return out


def duplicates(task: Path, files):
    """A development copy of a file that already ships somewhere else.

    Only copies under authoring/ count. The rest of the identical pairs in a
    bundle are load-bearing: tests/pristine mirrors environment/app_src by
    definition, a solution file matching the shipped one is an artifact that
    needs no change, and two build contexts want the same .dockerignore. A
    variant is the reference with one decision changed, so its other files are
    identical by construction and reporting them teaches you to ignore this.
    """
    by = defaultdict(list)
    for p in files:
        rel = p.relative_to(task).as_posix()
        if rel.startswith("authoring/variants/"):
            continue
        by[hashlib.sha256(p.read_bytes()).hexdigest()].append(rel)
    out = []
    for group in by.values():
        if len(group) < 2:
            continue
        if not any(g.startswith("authoring/") for g in group):
            continue
        out.append("DUPLICATE  identical bytes: %s" % " == ".join(sorted(group)))
    return sorted(out)


OVERRIDE = re.compile(r"environ\.get\(|environ\[|getenv\(|shutil\.which\(|\bwhich\(")


def scope_of(body: str, line: int) -> str:
    """The code that would have to offer an alternative to this path.

    A path guarded by is_file() still leaves the next machine with no way to
    name its own, which is how the rejected bundle was written - the guard was
    there and the constant was still the only source. So the question is not
    "does it crash elsewhere" but "can the host say where its copy lives", and
    that is answered where the path is used: the enclosing function, or the
    module preamble when the path is a module-level constant.
    """
    try:
        tree = ast.parse(body)
    except SyntaxError:
        return body
    lines = body.splitlines()
    spans = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            spans.append((node.lineno, getattr(node, "end_lineno", node.lineno)))
    inner = [(a, b) for a, b in spans if a <= line <= b]
    if inner:
        a, b = min(inner, key=lambda s: s[1] - s[0])
        return "\n".join(lines[a - 1:b])
    covered = set()
    for a, b in spans:
        covered.update(range(a, b + 1))
    return "\n".join(t for i, t in enumerate(lines, 1) if i not in covered)


def hostpaths(task: Path, files):
    out = []
    for p in files:
        if p.suffix not in TEXT:
            continue
        try:
            body = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for pat, shown in HOST:
            hit = pat.search(body)
            if not hit:
                continue
            line = body[:hit.start()].count("\n") + 1
            where = scope_of(body, line) if p.suffix == ".py" else body
            if OVERRIDE.search(where):
                continue                 # the host can name its own; a probe, not a hardcode
            out.append("HOSTPATH   %s:%d names %s with no way for another host to "
                       "name its own" % (p.relative_to(task).as_posix(), line, shown))
            break
    return out


def scratch(task: Path, files):
    out = []
    for p in files:
        for label, test in SCRATCH:
            if test(p):
                out.append("SCRATCH    %s (%s)" % (p.relative_to(task).as_posix(), label))
                break
    return out


def check(slug: str) -> int:
    task = Path(slug) if Path(slug).is_dir() else TASKS / slug
    if not task.is_dir():
        print("== %s\n   no such task" % slug)
        return 2
    files = list(shipped(task))
    found = (scratch(task, files) + orphans(task, files)
             + duplicates(task, files) + hostpaths(task, files))
    print("== %s" % slug)
    for line in found:
        print("   " + line)
    if not found:
        print("   clean: every shipped file is reachable, distinct and host-free")
    return 1 if found else 0


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    slugs = ([p.name for p in sorted(TASKS.iterdir()) if p.is_dir()]
             if argv[1] == "--all" else argv[1:])
    return max(check(s) for s in slugs)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
