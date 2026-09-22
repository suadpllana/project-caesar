#!/usr/bin/env python3
"""Write the cheat scripts for the wrong readings and the slow-but-exact families. Never ships.

Each reading cheat is a whole submission - the reference with one decision taken the other way,
built by the asserted substitutions in readings.py - so a score of 0 is attributable to that
decision and not to four other things being wrong at once. Each slow cheat is one of the exact
implementations under slow/, which answer every program and cannot finish inside the clock.
Module docstrings are stripped on the way out: a cheat is a probe, not a place to restate the
solution.

Run this after every change to readings.py or the reference (CLAUDE.md, publish-settle-order:
a cheat emitted before the reading was repaired tests the unrepaired reading).

    python3 emit.py
"""
import ast
import stat
import sys

import lab
import readings

CHEATS = lab.TASK / "cheat"

# Correct and too slow, each named for the part of the fast path it leaves out. The third slow
# directory, no-row-cache, is exact and inside the clock, so it is a timing variant and not a
# cheat.
SLOW = {
    "full-relayout": "lays the whole tree out again for every question, which is exact and too slow",
    "scan-headers": "scans every pinned box on every pass to find the stuck ones, which is exact and too slow",
}


def strip(src):
    tree = ast.parse(src)
    if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant):
        end = tree.body[0].end_lineno
        src = "\n".join(src.splitlines()[end:]).lstrip("\n") + "\n"
    ast.parse(src)
    return src


def script(why, files):
    body = ["#!/bin/bash", "# " + why, "set -euo pipefail", ""]
    for part in lab.PARTS:
        body += ["cat > /app/view/%s <<'PYEOF'" % part, strip(files[part]).rstrip("\n"), "PYEOF", ""]
    text = "\n".join(body) + "\n"
    if "\r" in text:
        raise SystemExit("carriage return in a cheat")
    return text


def write(name, text):
    out = CHEATS / ("cheat-%s.sh" % name)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    out.chmod(out.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return out


def main(argv):
    CHEATS.mkdir(exist_ok=True)
    ref = readings.base()
    names = argv or list(readings.READINGS)
    wrote = 0
    for name in names:
        if name in SLOW:
            continue
        files = readings.build(name)
        changed = [p for p in lab.PARTS if files[p] != ref[p]]
        if not changed:
            raise SystemExit("%s replaces nothing" % name)
        write(name, script(readings.WHY[name], files))
        wrote += 1
    for name, why in SLOW.items():
        if argv and name not in argv:
            continue
        d = lab.HERE / "slow" / name
        files = {p: (d / p).read_text(encoding="utf-8") for p in lab.PARTS}
        if files == ref:
            raise SystemExit("slow/%s is the reference" % name)
        write(name, script(why, files))
        wrote += 1
    print("wrote %d cheats into %s" % (wrote, CHEATS))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
