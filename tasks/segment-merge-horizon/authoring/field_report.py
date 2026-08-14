#!/usr/bin/env python3
"""Which graded field separates which cheat, and whether any of them separates nothing.

A field that no wrong implementation ever diverges on is pure liability: it cannot catch a
wrong answer and it can still fail a right one, which is the run-audit failure. This runs
every cheat and every alternative correct implementation through the real runner and reports,
per graded field, how many cheats it catches and whether any correct variant disagrees with
the reference on it.

Usage:
    python3 authoring/field_report.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "authoring"))
sys.path.insert(0, str(TASK / "tests"))

import harness  # noqa: E402
import scen  # noqa: E402

FIELDS = ("view", "snaps", "reads", "writes", "probes", "trace", "jobs")
NAMES = [s["name"] for s in scen.SCENARIOS]


def load_gt():
    return json.loads((TASK / "tests" / "gt.json").read_text())["scenarios"]


def diverges(rep, exp, field):
    got = rep.get(field)
    if field in ("reads", "writes", "probes"):
        return not (isinstance(got, int) and got <= exp[field])
    return got != exp[field]


def main() -> int:
    gt = load_gt()
    caught = dict((f, []) for f in FIELDS)
    trouble = []

    for d in sorted((TASK / "authoring" / "cheatsrc").glob("*")):
        if not d.is_dir():
            continue
        data = harness.run("authoring/cheatsrc/" + d.name)
        for f in FIELDS:
            hit = 0
            for name in NAMES:
                rep = (data.get("reports") or {}).get(name)
                if rep is None or diverges(rep, gt[name], f):
                    hit += 1
            if hit:
                caught[f].append("%s:%d" % (d.name, hit))

    for d in sorted((TASK / "authoring" / "variants").glob("ok-*")):
        data = harness.run("authoring/variants/" + d.name)
        for f in FIELDS:
            for name in NAMES:
                rep = (data.get("reports") or {}).get(name)
                if rep is None or diverges(rep, gt[name], f):
                    trouble.append("%s disagrees on %s in %s" % (d.name, f, name))

    dead = []
    for f in FIELDS:
        hits = caught[f]
        if not hits:
            dead.append(f)
        print("%-8s catches %2d cheats  %s"
              % (f, len(hits), ", ".join(hits[:5]) + (" ..." if len(hits) > 5 else "")))

    print()
    for t in trouble:
        print("TROUBLE", t)
    if dead:
        print("DEAD WEIGHT: %s - graded and separating nothing" % ", ".join(dead))
    if not dead and not trouble:
        print("every graded field separates at least one cheat, and no correct variant "
              "disagrees with the reference on any of them")
    return 1 if (dead or trouble) else 0


if __name__ == "__main__":
    sys.exit(main())
