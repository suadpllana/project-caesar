"""Differential test: the reference against the naive oracle over random programs."""
import sys

import gen_rand
import lab

ROOT = lab.ROOT


def main(argv):
    n = int(argv[1]) if len(argv) > 1 else 400
    start = int(argv[2]) if len(argv) > 2 else 0
    shapes = ((40, 10, 3, 4), (70, 14, 2, 5), (30, 6, 2, 3), (90, 20, 4, 6), (50, 8, 5, 2))
    texts = []
    for i in range(n):
        ops, keys, vals, live = shapes[i % len(shapes)]
        texts.append(gen_rand.program(start + i, ops, keys, vals, live))
    ok = lab.tree(ROOT / "tasks" / "claim-stand-break" / "solution")
    naive = lab.tree(ROOT / "authoring" / "claim-stand-break" / "slow")
    a = lab.batch(ok, texts)
    b = lab.batch(naive, texts)
    bad = 0
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            bad += 1
            if bad <= 3:
                print("=== seed %d ===" % (start + i))
                print(texts[i])
                for j in range(max(len(x), len(y))):
                    xa = x[j] if j < len(x) else "<none>"
                    ya = y[j] if j < len(y) else "<none>"
                    print(("  %-28s %s" % (xa, ya)) + ("   <<<" if xa != ya else ""))
    print("%d of %d differ" % (bad, len(texts)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
