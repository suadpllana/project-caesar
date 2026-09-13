"""Differential fuzz: the naive spec against the blocked candidate."""
import random
import sys

sys.path.insert(0, ".")
import fast
import naive
import tree


def prog(rng, ops=60, start=None):
    out = []
    n = start if start is not None else rng.choice([0, 1, 5, 30, 80])
    live = []
    if n:
        out.append("bulk %d %d %d" % (n, rng.choice([1, 20, 40, 100]), rng.choice([1, 3, 40, 200])))
        live = ["k%d" % (i + 1) for i in range(n)]
    made = 0
    for _ in range(ops):
        k = rng.randrange(14)
        if k == 0 and len(live) < 400:
            made += 1
            rid = "x%d" % made
            at = rng.randrange(len(live) + 1)
            live.insert(at, rid)
            out.append("ins %d %s %d" % (at, rid, rng.choice([0, 5, 40, 90, 250, 700])))
        elif k == 1 and live:
            i = rng.randrange(len(live))
            out.append("del %s" % live.pop(i))
        elif k == 2 and len(live) > 1:
            i = rng.randrange(len(live))
            rid = live.pop(i)
            j = rng.randrange(len(live))
            live.insert(j, rid)
            out.append("move %s %d" % (rid, j))
        elif k == 3 and live:
            out.append("set %s %d" % (rng.choice(live), rng.choice([0, 10, 60, 130, 400])))
        elif k == 4:
            out.append("span %d" % rng.choice([1, 7, 20, 40, 120]))
        elif k in (5, 6, 7):
            out.append("roll %d" % rng.choice([-900, -300, -47, -1, 1, 23, 150, 400, 5000]))
        elif k in (8, 9, 10):
            out.append("pass")
        elif k == 11:
            out.append("top")
        elif k == 12:
            out.append("tall")
        else:
            out.append("face")
    out += ["top", "tall", "face"]
    return out


def main():
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    rng = random.Random(11)
    bad = 0
    for i in range(rounds):
        lines = prog(rng, ops=rng.choice([20, 60, 140]))
        a = naive.run(lines)
        b = fast.run(lines)
        c = tree.run(lines)
        if a != b or a != c:
            bad += 1
            if bad <= 2:
                print("DIFFER round", i)
                print("\n".join(lines))
                for x, y in zip(a, b if a != b else c):
                    if x != y:
                        print("  naive %r  other %r" % (x, y))
                        break
                print("  lens", len(a), len(b), len(c))
    print("%d/%d programs agreed" % (rounds - bad, rounds))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
