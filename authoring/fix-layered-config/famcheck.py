"""Every generated family through the reference and the model: agreement and cost.

    python3 famcheck.py [per] [seed]
"""
import pathlib
import random
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

TESTS = lab.TASK / "tests"
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(TESTS / "seal"))
import gen  # noqa: E402
import model  # noqa: E402


def main(argv):
    per = int(argv[0]) if argv else 5
    seed = argv[1] if len(argv) > 1 else "famcheck"
    lb = lab.Lab(lab.TASK / "solution")
    bad = 0
    tref = tmod = 0.0
    for name, fn in gen.FAMS + gen.SCALE:
        n = per if (name, fn) in gen.FAMS else 1
        r = m = 0.0
        for i in range(n):
            text = fn(random.Random("%s/%s/%d" % (seed, name, i)))
            t = time.time()
            got = lb.run(text)
            r += time.time() - t
            t = time.time()
            want = model.trace(text)
            m += time.time() - t
            if got != want:
                bad += 1
                diff = [(a, b) for a, b in zip(got, want) if a != b][:3]
                print("DIFFER %s-%d: %d lines differ, first %s" % (name, i, sum(a != b for a, b in zip(got, want)), diff))
        tref += r
        tmod += m
        print("%-16s %2d plans  ref %6.2fs  model %6.2fs" % (name, n, r, m), flush=True)
    lb.close()
    print("total ref %.1fs model %.1fs, %d disagreements" % (tref, tmod, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
