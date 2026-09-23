"""Differential test: fast app vs literal reference on random segment files."""
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "..", "app")
sys.path.insert(0, APP)
sys.path.insert(0, HERE)

import gen  # noqa: E402
import ref  # noqa: E402
import run_scan  # noqa: E402


def main():
    a = int(sys.argv[1])
    b = int(sys.argv[2])
    gmod = importlib.import_module(sys.argv[3]) if len(sys.argv) > 3 else gen
    bad = 0
    for seed in range(a, b):
        text = gmod.make(seed)
        want = ref.run(text)
        got = run_scan.run(text)
        if want != got:
            bad += 1
            if bad <= 3:
                path = os.path.join(HERE, "fail_%d.txt" % seed)
                with open(path, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(text)
                print("MISMATCH seed", seed, "->", path)
                for x, (w, g) in enumerate(zip(want, got)):
                    if w != g:
                        print("  first diff at line", x, "want", w, "got", g)
                        break
                else:
                    print("  length differs", len(want), len(got))
    print("done", b - a, "cases,", bad, "mismatches")


if __name__ == "__main__":
    main()
