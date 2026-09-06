"""The must-still-work half of the case list, searched rather than hand-written.

Every entry names a property the timeline has to show, and the trace that carries
it is found in the generated pool and shrunk while the property survives. A
property that no trace shows is reported rather than quietly dropped, because a
fence with nothing behind it is worse than no fence.

Usage: python3 authoring/batch-admit-reclaim/corners.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tasks", "batch-admit-reclaim", "tests"))

import carve
import gen
import play

WORK = os.environ.get("WORK", "/tmp/bar-work")


def kinds(rows, kind):
    return [r for r in rows if r[1] == kind]


PROPS = [
    ("nothing is ever put out", lambda rows: not kinds(rows, "preempt") and len(rows) >= 8),
    ("one request on its own", lambda rows: len(set(r[0] for r in rows)) == 1),
    ("two newcomers take what is already there",
     lambda rows: len([r for r in kinds(rows, "admit") if r[3] > 0]) >= 2),
    ("three requests are put out",
     lambda rows: len(kinds(rows, "preempt")) >= 3),
    ("a request comes back part way through",
     lambda rows: any(r[3] > 0 for r in kinds(rows, "resume"))),
    ("a request comes back with nothing kept",
     lambda rows: any(r[3] == 0 for r in kinds(rows, "resume"))),
    ("one finishes on the step another comes in",
     lambda rows: bool(set(r[2] for r in kinds(rows, "done"))
                       & set(r[2] for r in kinds(rows, "admit") + kinds(rows, "resume")))),
    ("a request is put out on the step it would have finished",
     lambda rows: bool(set(r[2] for r in kinds(rows, "preempt"))
                       & set(r[2] for r in kinds(rows, "done")))),
    ("a request is put out twice",
     lambda rows: any(len([r for r in kinds(rows, "preempt") if r[0] == i]) >= 2
                      for i in set(r[0] for r in rows))),
]


def main(argv):
    ref = play.reference(os.path.join(WORK, "ref"))
    pool = [t for _, t in gen.batch("corners", 900)]
    out = []
    for label, want in PROPS:
        def holds(text, want=want):
            rows = play.safe(ref, text)
            if not rows or rows[0][0] == "torn":
                return False
            return want(rows)

        hit = None
        for text in sorted(pool, key=len):
            if holds(text):
                hit = text
                break
        if hit is None:
            sys.stderr.write("NO TRACE for %s\n" % label)
            continue
        text = carve.shrink(hit, holds)
        sys.stderr.write("%-52s %3d lines\n" % (label, len(text.strip().splitlines())))
        out.append((label, text))
    print(carve.render(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
