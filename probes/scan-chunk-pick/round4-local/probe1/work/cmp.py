"""Compare the fast implementation against the literal model on random files."""
import os
import sys
import importlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "app"))

import gen  # noqa: E402
import model  # noqa: E402
import run_scan  # noqa: E402


def main():
    a = int(sys.argv[1])
    b = int(sys.argv[2])
    big = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    bad = 0
    for seed in range(a, b):
        text = gen.make(seed, big)
        try:
            want = model.run(text)
        except AssertionError as e:
            print("MODEL ASSERT", seed, e)
            bad += 1
            continue
        got = run_scan.run(text)
        if want != got:
            bad += 1
            print("DIFF seed", seed)
            with open(os.path.join(HERE, "fail_%d.txt" % seed), "w", newline="\n") as fh:
                fh.write(text)
            if bad > 5:
                break
    print("done", b - a, "bad", bad)


if __name__ == "__main__":
    main()
