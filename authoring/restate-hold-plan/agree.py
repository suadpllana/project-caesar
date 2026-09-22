#!/usr/bin/env python3
"""Does the reference print what the sealed model prints, everywhere? Never ships.

The two were written apart - the model recursive with a memo, the reference iterative over a set
settled in time order - so agreement across the enumerated set and many generated populations is
evidence for both. Timings are printed per family, because the large families are what the 60
second clock is about.

    python3 -u authoring/restate-hold-plan/agree.py [seeds] [each] [policy-dir]
"""
import sys
import time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402


def main():
    seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    each = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    policy = sys.argv[3] if len(sys.argv) > 3 else str(lab.SOL)
    cases, gen, model = lab.sealed()
    here = lab.tree(policy)
    bad = 0
    for name in cases.ORDER:
        if lab.run_text(here, "\n".join(cases.prog(name)) + "\n") != model.expect(cases.prog(name)):
            bad += 1
            print("DIFFERS on enumerated %s" % name, flush=True)
    spent, count = defaultdict(float), defaultdict(int)
    for s in range(seeds):
        for fam, name, lines in gen.programs("agree-%d" % s, each):
            t0 = time.time()
            got = lab.run_text(here, "\n".join(lines) + "\n")
            spent[fam] += time.time() - t0
            count[fam] += 1
            if got != model.expect(lines):
                bad += 1
                print("DIFFERS on %s (seed %d)" % (name, s), flush=True)
    for fam, _big in gen.FAMILIES:
        print("%-7s %4d programs  %6.2fs" % (fam, count[fam], spent[fam]))
    total = sum(spent.values()) / max(1, seeds)
    print("%d disagreements; %.1fs of planning per graded set" % (bad, total))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
