"""Write the cheat scripts for the wrong readings.

Each one is a whole submission - the reference with a single decision taken the other way - so
a score of 0 is attributable to that decision and not to four other things being wrong at the
same time. The module docstrings are stripped on the way out: a cheat script is a probe, not a
place to restate the solution.
"""
import ast
import pathlib
import stat
import sys

import lab

HERE = pathlib.Path(__file__).resolve().parent
CHEATS = lab.TASK / "cheat"

WHY = {
    "boots-after-closure": "publishes the whole closure, then runs every startup call",
    "boot-before-publish": "runs a unit's startup calls before it is published",
    "uses-survive": "lets a returning unit keep what it settled in its last life",
    "reup-moves": "moves a unit to the back of the order when it is brought up again",
    "reup-no-hold": "adds no hold when a unit that is already up is brought up again",
    "needs-sorted": "takes what a unit names in sorted order rather than declaration order",
    "pre-skipped": "brings up only hard dependencies and ignores the ordering edges",
    "pre-after-deps": "takes the hard dependencies first and the ordering edges after them",
    "open-is-act": "publishes an `open` activation public, as if scopes did not exist",
    "scope-per-unit": "gives every unit of an `open` activation a scope of its own",
    "no-promotion": "leaves a publication private when `act` names it again",
    "see-everything": "lets every caller read every scope",
    "scope-only": "lets a caller in a scope read that scope and not the public publications",
    "promote-at-back": "puts a promoted publication at the back of the public order",
    "strong-over-fallback": "prefers an ordinary publication to a fallback one",
    "newest-publisher": "answers a name with the newest publisher rather than the first",
    "scan-the-order": "answers every call by scanning the publication order, which is correct and too slow",
    "global-list-filtered": "keeps one list per name and filters it by visibility, which is correct and too slow",
    "same-name-same-unit": "treats a returning unit as the publication a use settled on",
    "settle-the-miss": "settles a call that found nothing, so it can never settle later",
    "resolve-each-call": "resolves every call afresh instead of settling once",
    "dead-rebinds": "resolves again once the publication a use settled on has gone",
    "call-when-down": "lets a unit that is not up make a call",
    "sweep-forward": "takes the first unwanted unit in publication order rather than the last",
    "sweep-drop-stale": "never looks again at a unit the cascade has just freed",
    "sweep-rescan": "finds each candidate by scanning the live set, which is correct and too slow",
    "rel-any-unit": "gives back a hold from a unit that is not up or holds none",
    "deps-need-not-live": "never gives back what a retired unit was holding",
    "soft-keeps": "lets an ordering edge keep its target up, like a dependency",
    "dedupe-once": "counts every edge on the way in and one per name on the way out",
    "holds-only": "ignores live dependents and keeps a unit only for its own holds",
    "want-scan": "answers every retention question by scanning the live set, which is correct and too slow",
}


def strip(src):
    tree = ast.parse(src)
    if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant):
        end = tree.body[0].end_lineno
        return "\n".join(src.splitlines()[end:]).lstrip("\n")
    return src


def script(name):
    reading = HERE / "readings" / name
    if not reading.is_dir():
        raise SystemExit("no reading %s" % name)
    body = ["#!/bin/bash", "# " + WHY[name], "set -euo pipefail", ""]
    fired = 0
    for part in lab.PARTS:
        one = reading / part
        if one.is_file():
            src = one.read_text()
            if src == (lab.TASK / "solution" / part).read_text():
                raise SystemExit("%s/%s is identical to the reference" % (name, part))
            fired += 1
        else:
            src = strip((lab.TASK / "solution" / part).read_text())
        body += ["cat > /app/link/%s <<'PYEOF'" % part, src.rstrip("\n"), "PYEOF", ""]
    if not fired:
        raise SystemExit("%s replaces nothing" % name)
    return "\n".join(body) + "\n"


def main(argv):
    CHEATS.mkdir(exist_ok=True)
    names = argv or sorted(WHY)
    for name in names:
        out = CHEATS / ("cheat-%s.sh" % name)
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(script(name))
        out.chmod(out.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print("wrote", out.name)


if __name__ == "__main__":
    main(sys.argv[1:])
