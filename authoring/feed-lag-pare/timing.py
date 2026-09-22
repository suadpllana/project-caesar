"""Time the reference, the correct variants and the two correct-but-slow readings.

The execution limit is the only thing that separates them, so it is the one number in the
brief that has to be measured rather than guessed. Every tree here is run the way the worker
runs it: the tree is staged once, `run_log` is imported once, and then every graded program
goes through it - import churn is not part of what the limit measures.

    python3 -u authoring/feed-lag-pare/timing.py [per] [name ...]
"""
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

cases, gen, _model = lab.sealed()

emit.slow_rebuild()
emit.slow_repick()

TREES = {
    "reference": lab.SOL,
    "ok-flat": HERE / "variants" / "ok-flat",
    "ok-effect": HERE / "variants" / "ok-effect",
}
FILES = {
    "slow-rebuild": emit.BUILT["slow-rebuild"],
    "slow-repick": emit.BUILT["slow-repick"],
}
# The pair table re-formed after every collapse is quadratic in the number of collapses, and
# the wide family makes that unbounded, so it is timed on the deep family alone and reported
# as such. A number that never came back is not a measurement.
ONLY = {"slow-repick": ("deep",)}


def main():
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    want = sys.argv[2:] or (list(TREES) + list(FILES))
    work = [("hand", name, cases.prog(name)) for name in cases.ORDER]
    work += gen.programs("timing", per)
    print("%d programs" % len(work), flush=True)
    for name in want:
        here = lab.tree(TREES[name]) if name in TREES else lab.tree(None, FILES[name])
        mod = lab.inproc(here)
        spent = {}
        only = ONLY.get(name)
        for fam, _n, lines in work:
            if only and fam not in only:
                continue
            start = time.time()
            mod.run("\n".join(lines) + "\n")
            spent[fam] = spent.get(fam, 0.0) + time.time() - start
        total = sum(spent.values())
        heavy = sorted(spent, key=lambda f: -spent[f])[:3]
        print("%-14s %7.2fs   %s" % (name, total,
                                     "  ".join("%s %.1fs" % (f, spent[f]) for f in heavy)),
              flush=True)


if __name__ == "__main__":
    main()
