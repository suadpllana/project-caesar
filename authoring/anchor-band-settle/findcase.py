#!/usr/bin/env python3
"""Search small one-frame programs for one that separates a named reading. Never ships.

The found program is only a starting point: it is then simplified and traced by hand before it
goes into tests/cases.py.

    python3 findcase.py <reading> [tries] [seed]
"""
import random
import sys

import lab
import readings

cases, gen, model = lab.sealed()


def small(rng):
    vh = rng.choice([60, 80, 100, 120])
    lines = ["view %d" % vh]
    n = [0]

    def fresh(tag):
        n[0] += 1
        return "%s%d" % (tag, n[0])

    ids = []
    for _ in range(rng.randint(1, 3)):
        sec = fresh("s")
        lines.append("box %s - %d" % (sec, rng.choice([0, 0, 10])))
        ids.append(sec)
        if rng.random() < 0.8:
            h = fresh("h")
            lines.append("box %s %s %d pin=%d" % (h, sec, rng.choice([10, 20, 30]), rng.choice([0, 0, 10, 20, 30, 50])))
            ids.append(h)
        for _ in range(rng.randint(1, 4)):
            if rng.random() < 0.3:
                p = fresh("p")
                lines.append("box %s %s %d" % (p, sec, rng.choice([0, 10])))
                ids.append(p)
                if rng.random() < 0.6:
                    h = fresh("h")
                    lines.append("box %s %s %d pin=%d" % (h, p, rng.choice([10, 20]), rng.choice([10, 20, 30])))
                    ids.append(h)
                for _ in range(rng.randint(1, 3)):
                    r = fresh("r")
                    lines.append("box %s %s %d" % (r, p, rng.choice([10, 20, 30, 40])))
                    ids.append(r)
            else:
                r = fresh("r")
                lines.append("box %s %s %d" % (r, sec, rng.choice([10, 20, 30, 40, 60])))
                ids.append(r)
    world, _ = model.begin(lines + ["at 0"])
    lines.append("at %d" % rng.randint(0, max(0, world.span())))
    lines.append("frame")
    for _ in range(rng.randint(1, 2)):
        b = rng.choice(ids)
        k = rng.random()
        if k < 0.6:
            lines.append("size %s %d" % (b, rng.choice([0, 5, 10, 20, 40, 60, 80])))
        elif k < 0.75:
            lines.append("pin %s %d" % (b, rng.choice([0, 10, 20, 40])))
        elif k < 0.85:
            lines.append("unpin %s" % b)
        else:
            lines.append("drop %s" % b)
            break
    return lines


def main(argv):
    name = argv[1]
    tries = int(argv[2]) if len(argv) > 2 else 20000
    seed = argv[3] if len(argv) > 3 else "find"
    tree = lab.tree(files=readings.build(name))
    best = None
    for i in range(tries):
        rng = random.Random("%s|%s|%d" % (seed, name, i))
        lines = small(rng)
        try:
            want = model.expect(lines)
        except Exception:
            continue
        got = lab.run_text(tree, "\n".join(lines) + "\n")
        if got != want:
            if best is None or len(lines) < len(best[0]):
                best = (lines, want, got)
    if best is None:
        print("nothing found in %d tries" % tries)
        return 1
    lines, want, got = best
    print("\n".join(lines))
    print("# model   %s" % " | ".join(want))
    print("# reading %s" % " | ".join(got))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
