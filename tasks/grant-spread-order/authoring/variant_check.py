"""Every alternative correct implementation must score 1 through the real verifier.

This is the gate the run audit applies. A graded quantity that two correct implementations
disagree on is a trap rather than a test, and the way to find one is to write the other
implementations and run them.
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import trial  # noqa: E402


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    boxes = sorted((HERE / "variants").glob("ok-*"))
    if not boxes:
        print("no variants; run authoring/make_variants.py")
        return 1
    bad = 0
    for box in boxes:
        name, reward, text = trial.go(box.name, box, None, count)
        ok = reward == 1
        bad += 0 if ok else 1
        print("%s %-18s reward %d" % ("ok " if ok else "BAD", box.name, reward))
        if not ok:
            print("   ", trial.first_failure(text))
    print("\n%d of %d alternative correct implementations score 1"
          % (len(boxes) - bad, len(boxes)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
