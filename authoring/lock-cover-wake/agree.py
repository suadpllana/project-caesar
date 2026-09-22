#!/usr/bin/env python3
"""Reference against the sealed model over the generated families. Never ships.

    python3 -u authoring/lock-cover-wake/agree.py [per] [seed] [--only fam]
"""
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

cases, gen, model = lab.sealed()


def main():
    argv = sys.argv[1:]
    only = None
    if "--only" in argv:
        i = argv.index("--only")
        only = argv[i + 1]
        del argv[i:i + 2]
    per = int(argv[0]) if argv else 12
    seed = argv[1] if len(argv) > 1 else "agree"
    here = lab.tree(policy=str(lab.SOL))
    work = [w for w in gen.programs(seed, per) if only is None or w[0] == only]
    bad = 0
    tref = tmod = 0.0
    seen = {}
    for fam, name, lines in work:
        t0 = time.time()
        got = lab.run_text(here, "\n".join(lines) + "\n")
        t1 = time.time()
        want = model.expect(lines)
        t2 = time.time()
        tref += t1 - t0
        tmod += t2 - t1
        slot = seen.setdefault(fam, [0, 0, 0.0, 0])
        slot[0] += 1
        slot[2] += t1 - t0
        slot[3] += len(lines)
        if got != want:
            bad += 1
            slot[1] += 1
            if bad <= 2:
                print("--- %s" % name)
                print("\n".join(lines[:60]))
                for k in range(max(len(got), len(want))):
                    g = got[k] if k < len(got) else "-"
                    w = want[k] if k < len(want) else "-"
                    if g != w:
                        print("  line %d: reference %-30s model %s" % (k, g, w))
    for fam in sorted(seen):
        n, wrong, secs, size = seen[fam]
        print("%-8s %3d scripts %6d lines  reference %7.2fs  wrong %d"
              % (fam, n, size, secs, wrong))
    print("total reference %.2fs   model %.2fs   %d of %d differ"
          % (tref, tmod, bad, len(work)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
