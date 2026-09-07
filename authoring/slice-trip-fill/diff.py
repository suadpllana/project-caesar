import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gen
import model
import readings


def tree(text):
    return list(readings.run(readings.REFERENCE, text))


def main(argv):
    seed = argv[1] if len(argv) > 1 else "s0"
    n = int(argv[2]) if len(argv) > 2 else 400
    bad = 0
    for name, text in gen.batch(seed, n):
        try:
            a = tree(text)
        except Exception as exc:
            print("TREE RAISED %s: %r" % (name, exc), flush=True)
            print(text)
            bad += 1
            continue
        try:
            b = model.solve(text)
        except Exception as exc:
            print("MODEL RAISED %s: %r" % (name, exc), flush=True)
            print(text)
            bad += 1
            continue
        b = [tuple(r) for r in b]
        if a != b:
            bad += 1
            print("MISMATCH %s" % name, flush=True)
            for i in range(max(len(a), len(b))):
                x = a[i] if i < len(a) else None
                y = b[i] if i < len(b) else None
                if x != y:
                    print("  row %d tree=%s model=%s" % (i, x, y))
                    break
            if bad <= 2:
                print(text)
    print("%s: %d sessions, %d disagreements" % (seed, n, bad), flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
