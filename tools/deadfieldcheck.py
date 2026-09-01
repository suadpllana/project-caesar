#!/usr/bin/env python3
"""Find attributes the environment writes and nothing ever reads.

This is the cheapest audit in the repo and it caught a real difficulty rejection.

`guard-mark-unwind` came back 0 of 8 on 2026-09-01. One of the four causes was two fields,
`Gd.own` and `Gd.kind`, that `loop.py` assigned and that no frozen file, no cheat, no
variant and not the reference ever read. The failing agent grepped for exactly that and
wrote, in its own words:

    they exist solely for the four files I can edit. That's a strong hint about the
    band/owner distinction

It then invented a rule out of them that no correct implementation has, and lost 73 of 300
graded programs on it. Deleting the two fields left `gt.json` byte-identical and every
shipped program's trace byte-identical, which is what proves they were dead.

`preflight.py` warns about unused public *functions* and says nothing about fields. A field
is the worse of the two: an uncalled function reads as dead code, while an unread field
reads as a clue, so a strong agent builds a rule on it precisely because it is dead.

Known limitation, and it is the one that hid the original defect: attribute names are
matched across the whole tree, not per class. `Gd.own` was dead, but `Bd.own` is read by
`loop.py`, so the shared name masks it and this check stays quiet on it. When two classes
share a field name, read their `__slots__` by eye as well. What it does catch on that same
bundle is `Gd.kind`, which is enough to send you looking.

Usage:
    python tools/deadfieldcheck.py <slug>
    python tools/deadfieldcheck.py --all

Exit code 0 if clean, 1 on any finding.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Attributes every Python object carries, or that the language itself reads.
IGNORE = {
    "__slots__", "__dict__", "__class__", "__name__", "__doc__", "__module__",
    "__init__", "__len__", "__iter__", "__enter__", "__exit__", "__repr__",
}


def walk(path: Path) -> tuple[dict[str, list[str]], set[str], set[str]]:
    """Return (attribute -> where written, genuinely read, only self-updated)."""
    writes: dict[str, list[str]] = {}
    reads: set[str] = set()
    bumped: set[str] = set()
    for p in sorted(path.rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        try:
            tree = ast.parse(p.read_text())
        except (SyntaxError, UnicodeDecodeError):
            continue
        # `x.n += 1` parses as a Store on x.n. It does read the old value, but only to
        # write it straight back, so a counter nothing else consults is still dead.
        for node in ast.walk(tree):
            if isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Attribute):
                bumped.add(node.target.attr)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Attribute) or node.attr in IGNORE:
                continue
            if isinstance(node.ctx, ast.Store):
                writes.setdefault(node.attr, []).append("%s:%d" % (p.name, node.lineno))
            else:
                reads.add(node.attr)
        # getattr(x, "name") and hasattr count as reads - a dynamic read is still a read.
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                    and node.func.id in ("getattr", "hasattr", "setattr"):
                for a in node.args[1:2]:
                    if isinstance(a, ast.Constant) and isinstance(a.value, str):
                        reads.add(a.value)
    return writes, reads, bumped


def check(task: Path) -> list[str]:
    env = task / "environment" / "app_src"
    if not env.is_dir():
        return []

    writes, env_reads, bumped = walk(env)

    # A field the reference reads is load-bearing, not dead: the agent has to discover it.
    # Anything a cheat or a variant reads is likewise in genuine use.
    other_reads: set[str] = set()
    for extra in (task / "solution", task / "authoring" / "variants", task / "cheat"):
        if extra.is_dir():
            other_reads |= walk(extra)[1]

    found = []
    for attr, where in sorted(writes.items()):
        if attr in env_reads or attr in other_reads:
            continue
        how = ("only ever updated in place and never consumed" if attr in bumped
               else "read nowhere")
        found.append(
            "%s: written at %s, %s - not in the environment, the reference, the variants or "
            "the cheats. Delete it, or make something read it. An unread field reads as a "
            "clue." % (attr, ", ".join(where[:3]), how)
        )
    return found


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    if argv[1] == "--all":
        tasks = sorted(p for p in (REPO / "tasks").iterdir() if p.is_dir())
    else:
        tasks = [Path(argv[1]) if Path(argv[1]).is_dir() else REPO / "tasks" / argv[1]]

    bad = 0
    for task in tasks:
        if not task.is_dir():
            print("no such task: %s" % task)
            return 2
        found = check(task)
        if found:
            bad += 1
            print("%s:" % task.name)
            for f in found:
                print("  %s" % f)
        else:
            print("%s: clean" % task.name)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
