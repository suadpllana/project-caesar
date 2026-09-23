"""Compare the scanner in ../app against ref.py on files from gen2."""
import importlib
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(os.path.dirname(HERE), "app")
sys.path.insert(0, HERE)

import gen2  # noqa: E402
import ref  # noqa: E402

for name in list(sys.modules):
    if name == "scn" or name.startswith("scn."):
        del sys.modules[name]
sys.path.insert(0, APP)
run_scan = importlib.import_module("run_scan")
assert run_scan.__file__.startswith(APP), run_scan.__file__


def main():
    shape = sys.argv[1]
    lo = int(sys.argv[2])
    hi = int(sys.argv[3])
    bad = 0
    tr = tf = 0.0
    for seed in range(lo, hi):
        text = gen2.make(seed, shape)
        t = time.time()
        want = ref.run(text)
        tr += time.time() - t
        t = time.time()
        got = run_scan.run(text)
        tf += time.time() - t
        if want != got:
            bad += 1
            print("MISMATCH", shape, seed, flush=True)
            for i, (a, b) in enumerate(zip(want, got)):
                if a != b:
                    print("  line", i, "want", a, "got", b, flush=True)
                    break
    print(shape, "seeds", hi - lo, "mismatches", bad,
          "ref %.1fs fast %.2fs" % (tr, tf), flush=True)


if __name__ == "__main__":
    main()
