"""Differential test: app (in one process, like the grader) against model.py."""
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(os.path.dirname(HERE), "app")
sys.path.insert(0, APP)
sys.path.insert(0, HERE)

import run_scan  # noqa: E402
import model  # noqa: E402
import gen  # noqa: E402


def main():
    kind = sys.argv[1]
    n = int(sys.argv[2])
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    rng = random.Random(seed)
    bad = 0
    ta = tm = 0.0
    lines = 0
    for i in range(n):
        if kind == "small":
            text = gen.gen(rng)
        elif kind == "wide":
            text = gen.wide_like(rng, N=rng.choice([300, 800, 1500]))
        elif kind == "deep":
            text = gen.deep_like(rng, N=rng.choice([1000, 3000]))
        else:
            raise SystemExit("kind?")
        t0 = time.time()
        a = run_scan.run(text)
        t1 = time.time()
        m = model.run(text)
        t2 = time.time()
        ta += t1 - t0
        tm += t2 - t1
        lines += len(m)
        if a != m:
            bad += 1
            path = os.path.join(HERE, "fail_%s_%d_%d.txt" % (kind, seed, i))
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            if bad <= 3:
                for k, (x, y) in enumerate(zip(a, m)):
                    if x != y:
                        print("case %d first diff at line %d: app=%r model=%r" % (i, k, x, y))
                        break
                else:
                    print("case %d length differs app=%d model=%d" % (i, len(a), len(m)))
                print("  saved", path)
    print("%s seed=%d cases=%d bad=%d lines=%d app=%.2fs model=%.2fs" % (kind, seed, n, bad, lines, ta, tm))


if __name__ == "__main__":
    main()
