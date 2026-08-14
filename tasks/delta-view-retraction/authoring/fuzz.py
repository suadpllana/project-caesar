#!/usr/bin/env python3
"""Differential fuzz: the reference against the sealed oracle, on random change streams.

The twelve scenarios are aimed at particular readings of the rule. They are not evidence
that the reference is correct in general, and the budget the verifier grades comes from
the reference, so a reference that is subtly wrong sets a budget a correct submission
cannot meet. This is the check that stands behind that number.

Every scenario is replayed through the real engine with the reference router overlaid, and
the final view and every emitted value are compared against oracle.Truth, which folds each
aggregate over the full surviving multiset with no cap and no accumulator. A mismatch
means the reference is wrong, not that the fuzz is wrong.

Usage:
    python3 authoring/fuzz.py [count] [seed]
"""

from __future__ import annotations

import random
import shutil
import sys
import tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "authoring"))

import harness  # noqa: E402
import oracle  # noqa: E402

BASE = {"lag": 2, "carry": 4,
        "view": {"sum": ["ord"], "cnt": ["ord"], "min": ["ord"], "max": ["ord"],
                 "top": ["ord"]}}


def stream(rng):
    """A change stream aimed at the cap boundary: duplicates, churn, group moves."""
    groups = ["g1", "g2"][:rng.randrange(1, 3)]
    keys = ["k%d" % i for i in range(rng.randrange(3, 10))]
    vals = list(range(1, rng.choice([4, 6, 12])))
    ops = []
    live = {}
    ts = 1
    for _ in range(rng.randrange(4, 26)):
        if rng.random() < 0.25:
            ts += rng.randrange(0, 3)
        k = rng.choice(keys)
        roll = rng.random()
        if roll < 0.5 or k not in live:
            g = rng.choice(groups)
            v = rng.choice(vals)
            ops.append({"op": "ins", "src": "ord", "k": k, "g": g, "v": v, "ts": ts})
            live[k] = g
        elif roll < 0.75:
            ops.append({"op": "del", "src": "ord", "k": k, "ts": ts})
            live.pop(k, None)
        else:
            rec = {"op": "upd", "src": "ord", "k": k, "v": rng.choice(vals), "ts": ts}
            if rng.random() < 0.4:
                rec["g"] = rng.choice(groups)
                live[k] = rec["g"]
            ops.append(rec)
    return ops


def drop():
    for name in list(sys.modules):
        if name.split(".")[0] in ("view", "store", "ingest"):
            sys.modules.pop(name, None)


def main(argv):
    count = int(argv[1]) if len(argv) > 1 else 600
    seed = int(argv[2]) if len(argv) > 2 else 11
    rng = random.Random(seed)

    tmp = Path(tempfile.mkdtemp())
    try:
        app = tmp / "app"
        harness.overlay("solution/ref", app)
        sys.path.insert(0, str(app))

        bad = 0
        values = 0
        for i in range(count):
            ops = stream(rng)
            drop()
            from view import drv
            d = drv.Drv(dict(BASE))
            rep = d.run(ops)

            t = oracle.Truth(dict(BASE))
            t.run(ops)
            values += len(t.log)
            if rep["view"] != t.view():
                bad += 1
                print("MISMATCH view on stream %d\n  ref %s\n  ora %s"
                      % (i, rep["view"], t.view()))
            elif [list(x) for x in rep["log"]] != [list(x) for x in t.log]:
                bad += 1
                print("MISMATCH emitted values on stream %d" % i)
            if bad >= 3:
                break
        print("%d streams, %d published values compared, %d mismatches"
              % (count, values, bad))
        return 1 if bad else 0
    finally:
        sys.path[:] = [p for p in sys.path if not p.startswith(str(tmp))]
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
