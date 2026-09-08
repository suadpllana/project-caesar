"""Timing: the reference against the shipped tree, and against a recompute-everything variant.

The execution limit is only fair if it is measured. This runs the wide family under each and
prints seconds, so the number quoted in the brief comes from a run rather than a guess.

    python3 authoring/space-charge-shift/timing.py [which]
"""
import sys
import time

import harness

sys.path.insert(0, harness.TESTS)
import gen  # noqa: E402
import model  # noqa: E402

HERE = __file__.rsplit("/", 1)[0]

TREES = {
    "reference": harness.TASK + "/solution",
    "shipped": None,
    "naive": HERE + "/naive",
}


def timed(dst, script):
    t0 = time.time()
    harness.run(dst, script)
    return time.time() - t0


def main(argv):
    seed = argv[1] if len(argv) > 1 else "probe"
    progs = [(nm, lines) for fam, nm, lines in gen.programs(seed, 1) if fam == "wide"]
    names = argv[2:] or sorted(TREES)
    print("wide scripts: %s" % ", ".join("%s(%d lines)" % (n, len(l)) for n, l in progs))
    for which in names:
        pol = TREES.get(which, which)
        dst = harness.tree(policy=pol)
        tot = 0.0
        for nm, lines in progs:
            script = gen.ops(lines)
            dt = timed(dst, script)
            tot += dt
            print("  %-12s %-10s %6.2fs" % (which, nm, dt), flush=True)
        print("  %-12s TOTAL      %6.2fs" % (which, tot), flush=True)
    t0 = time.time()
    for nm, lines in progs:
        model.run(gen.ops(lines))
    print("  %-12s TOTAL      %6.2fs" % ("model", time.time() - t0))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
