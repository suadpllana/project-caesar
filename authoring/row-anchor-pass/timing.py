#!/usr/bin/env python3
"""Time the reference and the naive-but-correct geometry on the two scale families.

The resource gate is only a gate once both sides are measured: the principled route has to
pass with headroom and the naive family has to fail at the stated scale. The naive tree under
naive/ is the reference with one file swapped - a flat prefix array over the whole flow,
rebuilt whenever a height moves, binary searched otherwise. It gives the reference's answers on
every program it finishes - run against the sealed model over 90 generated documents on
2026-09-22, none differing - so only the clock separates them.

Output goes through -u and flush so a long run does not look like a hang.

    python3 -u authoring/row-anchor-pass/timing.py [rounds]
"""
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
import gen  # noqa: E402

LIMIT = 60


def main():
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    progs = [p for p in gen.programs("timing", 1) if p[0] in ("wide", "deep")]
    for label, policy in (("reference", lab.SOL), ("naive", HERE / "naive"),
                          ("shipped", None)):
        here = lab.tree(policy)
        mod = lab.inproc(here)
        for fam, name, lines in progs:
            if label == "shipped" and fam in ("wide", "deep"):
                print("   %-9s %-8s not timed: the per-call walk does not finish"
                      % (label, fam), flush=True)
                continue
            text = "\n".join(lines) + "\n"
            best = None
            for _ in range(rounds):
                t0 = time.time()
                mod.run(text)
                dt = time.time() - t0
                best = dt if best is None else min(best, dt)
            print("   %-9s %-8s %7.2fs   %5.1f%% of the %ds limit"
                  % (label, name, best, 100 * best / LIMIT, LIMIT), flush=True)


if __name__ == "__main__":
    main()
