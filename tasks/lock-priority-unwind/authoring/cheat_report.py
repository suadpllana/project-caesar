#!/usr/bin/env python3
"""Which assertion catches each cheat, and on which scenario.

A cheat scoring 0 proves nothing on its own. It has to fail on the axis it was aimed at: a
policy mistake caught only by an import error, or by the tree hash rather than by the schedule,
has been rejected by nothing and the mistake it was named for is still unmeasured.

The line worth reading is the one for hand-back-the-schedule. It should pass every written
scenario and fail the drawn ones, because that is the entire argument for drawing scenarios at
verification time rather than recording them.

Usage:
    python3 authoring/cheat_report.py [name ...]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "authoring"))

import trial  # noqa: E402

FAIL = re.compile(r"^FAILED (?:.*::)?(\w+)\[?([^\]]*)\]?", re.M)


def summarise(tail: str) -> str:
    hits = FAIL.findall(tail)
    if not hits:
        return "no FAILED lines - check that it ran at all"
    axes = {}
    for test, case in hits:
        axes.setdefault(test, []).append(case)
    parts = []
    for test, cases in sorted(axes.items(), key=lambda kv: -len(kv[1])):
        parts.append("%s x%d (%s)" % (test, len(cases), cases[0] if cases[0] else "-"))
    return "; ".join(parts[:3])


def main(argv: list[str]) -> int:
    wanted = set(argv[1:])
    rows = []
    for f in sorted((TASK / "cheat").glob("cheat-*.sh")):
        name = f.stem[len("cheat-"):]
        if wanted and name not in wanted:
            continue
        reward, tail = trial.grade("cheat/" + f.name)
        rows.append((name, reward, summarise(tail)))
    for name, reward, why in rows:
        print("%s%-38s reward=%d  %s" % ("    " if reward == 0 else "!!! ", name, reward, why))
    bad = [r for r in rows if r[1] != 0]
    print("")
    print("%d of %d scored 1 and should not have" % (len(bad), len(rows)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
