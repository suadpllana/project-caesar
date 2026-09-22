#!/usr/bin/env python3
"""Search for the sample script whose one wrong line gives the least away. Never ships.

The brief has to quote one line of one shipped script, or a format slip fails every case for a
reason that is not the task. That line is also the only correct output the agent is handed, so
it is searched for rather than chosen: among the short scripts where the shipped engine differs
from the reference on exactly one line, the one whose line the fewest wrong readings also get
wrong.

    python3 -u authoring/lock-cover-wake/pick_tiny.py [rounds]
"""
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

cases, gen, model = lab.sealed()

SMALL = [f for f, big in gen.FAMILIES if not big]


def candidates(rounds):
    ship = lab.tree()
    ref = lab.tree(policy=str(lab.SOL))
    out = []
    for i in range(rounds):
        fam = SMALL[i % len(SMALL)]
        rng = random.Random("tiny|%d" % i)
        lines = gen.build(fam, rng)
        if len(lines) > 16:
            continue
        text = "\n".join(lines) + "\n"
        a = lab.run_text(ship, text)
        b = lab.run_text(ref, text)
        if len(a) != len(b):
            continue
        off = [k for k in range(len(a)) if a[k] != b[k]]
        if len(off) != 1:
            continue
        out.append((len(lines), fam, lines, a, b, off[0]))
    out.sort(key=lambda c: c[0])
    return out


def main():
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    for build in emit.READING_BUILDERS:
        build()
    pool = candidates(rounds)
    print("%d scripts differ from the shipped engine on exactly one line" % len(pool))

    trees = {name: lab.tree(files=files) for name, files in emit.READINGS.items()}
    best = []
    for size, fam, lines, a, b, k in pool[:60]:
        text = "\n".join(lines) + "\n"
        told = []
        for name, here in trees.items():
            got = lab.run_text(here, text)
            if len(got) <= k or got[k] != b[k]:
                told.append(name)
        best.append((len(told), size, fam, lines, a[k], b[k], k, told))
    best.sort(key=lambda c: (c[0], c[1]))
    for told, size, fam, lines, was, now, k, names in best[:6]:
        print("\n--- %s, %d commands, line %d, %d readings also get it wrong"
              % (fam, size, k, told))
        print("    shipped %r  correct %r" % (was, now))
        print("    readings: %s" % ", ".join(sorted(names)[:8]))
        print("\n".join("      " + ln for ln in lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
