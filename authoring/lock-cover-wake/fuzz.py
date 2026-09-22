#!/usr/bin/env python3
"""Differential test: the reference against the sealed model. Never ships.

    python3 -u authoring/lock-cover-wake/fuzz.py [count] [seed]
"""
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests" / "seal"))
import model  # noqa: E402

TMODES = ("IS", "IX", "S", "SIX", "X")


def script(rng, tables=3, rows=4, txns=5, cmds=30):
    ids = rng.sample(range(1, 40), txns)
    out = ["cfg %d" % rng.randint(2, 5)]
    for tid in ids:
        out.append("beg %d" % tid)
    for _ in range(cmds):
        tid = rng.choice(ids)
        if rng.random() < 0.10:
            out.append("com %d" % tid)
            continue
        tbl = rng.randrange(tables)
        if rng.random() < 0.35:
            out.append("req %d %d %s" % (tid, tbl, rng.choice(TMODES)))
        else:
            out.append("req %d %d.%d %s" % (tid, tbl, rng.randrange(rows),
                                            rng.choice(("S", "X"))))
    return out


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    here = lab.tree(policy=str(lab.SOL))
    rng = random.Random(seed)
    bad = 0
    for i in range(count):
        lines = script(rng,
                       tables=rng.randint(1, 3),
                       rows=rng.randint(2, 5),
                       txns=rng.randint(2, 6),
                       cmds=rng.randint(6, 40))
        got = lab.run_text(here, "\n".join(lines) + "\n")
        want = model.expect(lines)
        if got != want:
            bad += 1
            if bad <= 3:
                print("--- script %d" % i)
                print("\n".join(lines))
                for k in range(max(len(got), len(want))):
                    g = got[k] if k < len(got) else "-"
                    w = want[k] if k < len(want) else "-"
                    print("   %-34s %s %s" % (g, "==" if g == w else "!=", w))
    print("%d of %d scripts differ" % (bad, count))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
