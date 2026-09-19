"""Print the shipped feeder's trace beside the reference's, for one shipped plan."""
from __future__ import annotations

import pathlib
import sys
import time

import lab


def main(names):
    plans = lab.APP / "plans"
    for name in names:
        text = (plans / (name + ".txt")).read_text(encoding="utf-8")
        t0 = time.time()
        good = lab.run(lab.reference(), text)
        took = time.time() - t0
        print("== %s   reference %.3f s, %d lines" % (name, took, len(good)), flush=True)
        for line in good:
            print("   ref  " + line[:200], flush=True)
        if name in ("tiny", "mixed"):
            bad = lab.run(lab.shipped(), text)
            for line in bad:
                print("   ship " + line[:200], flush=True)
            same = sum(1 for a, b in zip(good, bad) if a == b)
            print("   %d of %d lines agree" % (same, max(len(good), len(bad))), flush=True)


if __name__ == "__main__":
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    main(sys.argv[1:] or ["tiny", "mixed"])
