"""How the per-rank sweep and the event-driven settlement scale on deep programs."""
import random
import sys
import time

import harness

sys.path.insert(0, str(harness.TASK / "tests"))
import model  # noqa: E402


def deep(units, names, seed=7):
    rng = random.Random(seed)
    lines = []
    for x in range(names):
        lines.append("u0 own n%d" % x)
    for i in range(1, units):
        lines.append("u%d pull u%d *" % (i, i - 1))
        if rng.random() < 0.2:
            lines.append("u%d own n%d" % (i, rng.randrange(names)))
    lines.append("u%d ask n0" % (units - 1))
    return lines


def timed(fn, lines):
    t = time.time()
    out = fn(lines)
    return time.time() - t, out


def main():
    dst = harness.tree(harness.REF)
    go, drop = harness.in_proc(dst)
    for units, names in ((60, 6), (120, 6), (240, 6), (360, 8)):
        lines = deep(units, names)
        a, ra = timed(go, lines)
        b, rb = timed(model.expect, lines)
        assert ra == rb, (ra, rb)
        print("units=%-4d names=%-2d lines=%-5d  sweep %7.2fs   event %7.2fs   %5.1fx"
              % (units, names, len(lines), a, b, a / b if b else 0), flush=True)
    drop()


if __name__ == "__main__":
    main()
