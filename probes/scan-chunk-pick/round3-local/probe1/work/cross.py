"""Compare app/run_scan.run with model.run on generated files, in one process."""
import random
import sys
import time

HERE = __file__.rsplit("/", 1)[0]
sys.path.insert(0, HERE + "/../app")
sys.path.insert(0, HERE)

import gen  # noqa: E402
import model  # noqa: E402
import run_scan  # noqa: E402


def check(text, tag):
    a = run_scan.run(text)
    b = model.run(text)
    if a != b:
        path = HERE + "/fail_%s.txt" % tag
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y:
                print("MISMATCH", tag, "line", i, "app", x, "model", y, "->", path)
                break
        else:
            print("MISMATCH", tag, "length", len(a), len(b), "->", path)
        return False
    return True


def main():
    mode = sys.argv[1]
    count = int(sys.argv[2])
    seed0 = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    bad = 0
    lines = 0
    t = time.time()
    for s in range(seed0, seed0 + count):
        rng = random.Random(s)
        if mode == "small":
            text = gen.make(rng)
        elif mode == "wide":
            text = gen.make(rng, n=rng.randint(200, 500), k=5, chunk=(16, 40), page=(4, 12),
                            nq=3, ncond=8, big=True)
        elif mode == "deep":
            text = gen.make(rng, n=rng.randint(600, 1500), k=4, chunk=(150, 300), page=(30, 90),
                            nq=3, ncond=7, big=True)
        elif mode == "mixed":
            a = rng.randint(1, 20)
            text = gen.make(rng, n=rng.randint(20, 200), k=rng.randint(1, 5),
                            chunk=(a, a + rng.randint(0, 30)), page=(1, rng.randint(1, 12)),
                            nq=rng.randint(3, 8), ncond=rng.randint(1, 8))
        else:
            raise SystemExit("mode")
        if not check(text, "%s_%d" % (mode, s)):
            bad += 1
            if bad >= 5:
                break
        lines += len(text)
    print(mode, "files", count, "bad", bad, "secs %.1f" % (time.time() - t))


if __name__ == "__main__":
    main()
