"""Shrink a program down to the smallest one that still separates a reading.

The worked example in the brief and every hand case has to be searched for rather than
chosen: a program that happens to separate a rule is not evidence that the case named for
that rule is doing the work.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "tasks" / "anchor-mean-settle" / "tests"))
sys.path.insert(0, str(HERE / "lab"))

import gen  # noqa: E402
import probe  # noqa: E402
import tree as model  # noqa: E402

REF = str(HERE.parent.parent / "tasks" / "anchor-mean-settle" / "solution")


def splits(reading, cands):
    """Which of these programs does the reading get wrong?"""
    jobs = [("c%d" % i, c) for i, c in enumerate(cands)]
    got, err = probe.run(reading, jobs)
    if got is None:
        return []
    keep = []
    for i, c in enumerate(cands):
        try:
            if got.get("c%d" % i) != model.run(c):
                keep.append(c)
        except Exception:
            pass
    return keep


def shrink(reading, prog):
    best = prog
    moved = True
    while moved:
        moved = False
        cands = [best[:i] + best[i + 1:] for i in range(len(best))]
        ok = splits(reading, cands)
        if ok:
            best = min(ok, key=len)
            moved = True
    return best


def main():
    reading = "readings/" + sys.argv[1]
    fam = sys.argv[2] if len(sys.argv) > 2 else None
    pool = [l for f, _n, l in gen.programs("readings-seed", 12)
            if f not in ("wide", "deep") and (fam is None or f == fam)]
    hit = splits(reading, pool)
    if not hit:
        print("no program in the pool separates", sys.argv[1])
        return 1
    print("%d of %d separate it; shrinking the shortest" % (len(hit), len(pool)))
    small = shrink(reading, min(hit, key=len))
    print("%d lines:" % len(small))
    print("\n".join(small))
    print("\ntrace:", " | ".join(model.run(small)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
