"""Compare the scanner in ../app against ref.py on random segment files."""
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(os.path.dirname(HERE), "app")
sys.path.insert(0, HERE)

import gen  # noqa: E402
import ref  # noqa: E402

# ref.py put work/orig on sys.path for its own `scn`; load the app's scanner
# from ../app instead, as a fresh package.
for name in list(sys.modules):
    if name == "scn" or name.startswith("scn."):
        del sys.modules[name]
sys.path.insert(0, APP)
run_scan = importlib.import_module("run_scan")
assert run_scan.__file__.startswith(APP), run_scan.__file__


def main():
    lo = int(sys.argv[1])
    hi = int(sys.argv[2])
    bad = 0
    lines = 0
    for seed in range(lo, hi):
        text = gen.make(seed)
        want = ref.run(text)
        got = run_scan.run(text)
        lines += len(want)
        if want != got:
            bad += 1
            if bad <= 3:
                print("MISMATCH seed", seed)
                for i, (a, b) in enumerate(zip(want, got)):
                    if a != b:
                        print("  first diff at line", i, "want", a, "got", b)
                        break
                else:
                    print("  length", len(want), len(got))
    print("seeds", hi - lo, "mismatches", bad, "lines", lines)


if __name__ == "__main__":
    main()
