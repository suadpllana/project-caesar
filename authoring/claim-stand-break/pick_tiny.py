"""Search for the worked example, rather than choosing one.

The brief has to print one program's correct line or a format slip fails every case for a
reason that is not the task. That example is an oracle unless it is measured: a candidate is
only usable when the shipped engine gets it visibly wrong and when knowing the right answer
still does not decide any of the wrong readings.
"""
import sys

import gen_rand
import lab
import make_readings

LOOSE = {"base-now", "look-gone", "mine-hidden", "walk-limit", "drop-apply",
         "off-mark", "span-order"}


def main(argv):
    n = int(argv[1]) if len(argv) > 1 else 3000
    shapes = ((10, 6, 2, 2), (12, 6, 2, 3), (14, 8, 2, 3), (16, 8, 3, 3), (18, 10, 3, 3))
    texts = []
    for i in range(n):
        texts.append(gen_rand.program(700000 + i, *shapes[i % len(shapes)]))
    ok = lab.batch(lab.tree(lab.ROOT / "tasks" / "claim-stand-break" / "solution"), texts)
    ship = lab.batch(lab.tree(), texts)
    live = [i for i, (a, b) in enumerate(zip(ok, ship))
            if a != b and len(a) == len(b)
            and 1 <= sum(1 for x, y in zip(a, b) if x != y) <= 3
            and any(l.startswith("dead") for l in a)
            and any(l.startswith("span") for l in a)
            and any(l.startswith("read") for l in a)]
    print("%d of %d differ in one to three lines with every line kind shown" % (len(live), n))
    seps = {i: set() for i in live}
    for name, _reads, _case, _patch in make_readings.READINGS:
        got = lab.batch(lab.tree(make_readings.OUT / name), [texts[i] for i in live])
        for j, i in enumerate(live):
            if got[j] != ok[i]:
                seps[i].add(name)
    clean = sorted(live, key=lambda i: (len(seps[i]), len(texts[i].splitlines())))
    for i in clean[:6]:
        print("--- seed %d, %d ops, separates %s" % (700000 + i, len(texts[i].splitlines()),
                                                     sorted(seps[i]) or "nothing"))
    best = [i for i in clean if not seps[i]] or [i for i in clean if seps[i] <= LOOSE]
    if not best:
        print("no candidate: every one decides a reading")
        return 1
    pick = best[0]
    print("\n=== picked seed %d (%d ops, separates %s) ===" % (
        700000 + pick, len(texts[pick].splitlines()), sorted(seps[pick]) or "nothing"))
    print(texts[pick])
    for a, b in zip(ok[pick], ship[pick]):
        print("  %-26s %s" % (a, "" if a == b else "<- shipped prints %s" % b))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
