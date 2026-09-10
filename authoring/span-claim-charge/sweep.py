"""Run the generated population through the reference (and optionally the model), timed."""
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "span-claim-charge"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import fuzz  # noqa: E402
import gen  # noqa: E402


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "ref"
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 45
    seed = sys.argv[3] if len(sys.argv) > 3 else "s1"
    if which in ("ref", "both"):
        tree = fuzz.stage()
        sys.path.insert(0, str(tree))
        from base import feed
    if which in ("model", "both"):
        import model
    work = gen.programs(seed, per)
    print("programs %d  commands %d" % (len(work), sum(len(l) for _f, _n, l in work)), flush=True)
    fam_time = {}
    bad = 0
    for famname, name, lines in work:
        t0 = time.time()
        got = feed.run(lines) if which in ("ref", "both") else None
        t1 = time.time()
        want = model.expect(lines) if which in ("model", "both") else None
        t2 = time.time()
        cur = fam_time.setdefault(famname, [0.0, 0.0, 0])
        cur[0] += t1 - t0
        cur[1] += t2 - t1
        cur[2] += 1
        if got is not None and want is not None and got != want:
            bad += 1
            print("DIFFER %s" % name, flush=True)
            for i, (a, b) in enumerate(zip(got, want)):
                if a != b:
                    print("  line %d: ref %r model %r" % (i, a, b), flush=True)
                    break
            if len(got) != len(want):
                print("  lengths %d vs %d" % (len(got), len(want)), flush=True)
            if bad > 3:
                break
    total_ref = sum(v[0] for v in fam_time.values())
    total_mod = sum(v[1] for v in fam_time.values())
    for fam, (a, b, k) in fam_time.items():
        print("%-8s n=%-4d ref %7.2fs  model %7.2fs" % (fam, k, a, b), flush=True)
    print("TOTAL ref %.2fs  model %.2fs  differ %d" % (total_ref, total_mod, bad), flush=True)


if __name__ == "__main__":
    main()
