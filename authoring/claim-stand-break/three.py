"""Reference, sealed model and the naive oracle, over random programs."""
import sys

import gen_rand
import lab

sys.path.insert(0, str(lab.ROOT / "tasks" / "claim-stand-break" / "tests" / "seal"))
import model  # noqa: E402

SHAPES = ((40, 10, 3, 4), (70, 14, 2, 5), (30, 6, 2, 3), (90, 20, 4, 6), (50, 8, 5, 2),
          (60, 5, 2, 4))


def main(argv):
    n = int(argv[1]) if len(argv) > 1 else 500
    start = int(argv[2]) if len(argv) > 2 else 0
    texts = []
    for i in range(n):
        texts.append(gen_rand.program(start + i, *SHAPES[i % len(SHAPES)]))
    ok = lab.batch(lab.tree(lab.ROOT / "tasks" / "claim-stand-break" / "solution"), texts)
    naive = lab.batch(lab.tree(lab.ROOT / "authoring" / "claim-stand-break" / "slow"), texts)
    bad = 0
    kinds = {}
    for i, text in enumerate(texts):
        mine = model.expect(text.splitlines())
        for line in ok[i]:
            kinds[line.split()[0]] = kinds.get(line.split()[0], 0) + 1
        if not (ok[i] == naive[i] == mine):
            bad += 1
            if bad <= 2:
                print("=== seed %d ===\n%s" % (start + i, text))
                for j in range(max(len(ok[i]), len(naive[i]), len(mine))):
                    row = [x[j] if j < len(x) else "<none>" for x in (ok[i], naive[i], mine)]
                    print("  %-24s %-24s %-24s %s" % (row[0], row[1], row[2],
                                                      "<<<" if len(set(row)) > 1 else ""))
    print("lines seen: %s" % sorted(kinds.items()))
    print("%d of %d disagree" % (bad, len(texts)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
