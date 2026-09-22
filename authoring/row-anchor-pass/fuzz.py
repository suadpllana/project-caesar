"""Differential fuzz: random small documents through several panes, compared line for line.

    python3 fuzz.py [count] [seed] [pane ...]     panes default to: brute solution

A pane is `brute` (brute.py), `model` (tests/seal/model.py), `solution`, `shipped`, or a
directory holding six pane files. The first pane named is the one the others are held to.
"""
import random
import sys

import brute
import lab

sys.path.insert(0, str(lab.TASK / "tests" / "seal"))


def small(rng):
    vh = rng.choice([20, 30, 45, 60, 90, 140])
    over = rng.choice([0, 0, 1, 2, 3])
    pcap = rng.choice([1, 2, 3, 4, 5, 6])
    est = rng.choice([3, 6, 10, 18, 30, 60])
    cap = rng.choice([1, 2, 3, 5, 8, 12, 20, 40, 1000])
    lines = ["cfg %d %d %d %d %d" % (vh, over, pcap, est, cap)]
    ng = rng.randint(1, 6)
    n = {}
    gids = []
    reach = 0
    for k in range(ng):
        gid = k + 1 + rng.choice([0, 0, 10])
        while gid in n:
            gid += 1
        hh = rng.randint(1, 30)
        lo = rng.randint(1, 40)
        hi = lo + rng.choice([0, 0, 3, 10, 30])
        rows = rng.choice([0, 1, 2, 3, 5, 8, 12])
        lines.append("g %d %d %d %d %d" % (gid, hh, lo, hi, rows))
        n[gid] = rows
        gids.append(gid)
        reach += hh + rows * (lo + hi) // 2
    for _ in range(rng.randint(1, 16)):
        pick = rng.random()
        if pick < 0.35:
            lines.append("scroll %d" % rng.randint(-reach // 3 - 5, reach // 3 + 5))
        elif pick < 0.55:
            lines.append("go %d" % rng.randint(0, reach + 40))
        elif pick < 0.62:
            lines.append("size %d" % rng.choice([10, 25, 40, 70, 200]))
        elif pick < 0.81:
            gid = rng.choice(gids)
            k = rng.randint(1, 4)
            lines.append("ins %d %d %d" % (gid, rng.randint(0, n[gid]), k))
            n[gid] += k
        else:
            gid = rng.choice(gids)
            if n[gid] == 0:
                lines.append("scroll %d" % rng.choice([-1, 1]))
                continue
            k = rng.randint(1, n[gid])
            pos = rng.randint(0, n[gid] - k)
            lines.append("del %d %d %d" % (gid, pos, k))
            n[gid] -= k
    return lines


def load(name):
    if name == "brute":
        return brute.expect
    if name == "model":
        import model
        return model.expect
    return lab.pane(name)


def main(argv):
    count = int(argv[1]) if len(argv) > 1 else 2000
    seed = argv[2] if len(argv) > 2 else "fuzz"
    names = argv[3:] or ["brute", "solution"]
    panes = [(nm, load(nm)) for nm in names]
    rng = random.Random(seed)
    bad = {nm: 0 for nm in names[1:]}
    first = {}
    for c in range(count):
        doc = small(rng)
        want = panes[0][1](doc)
        for nm, run in panes[1:]:
            try:
                got = run(doc)
            except Exception as exc:  # noqa: BLE001
                got = ["raised %r" % exc]
            if got != want:
                bad[nm] += 1
                first.setdefault(nm, (doc, want, got))
    for nm in names[1:]:
        print("%-12s %d of %d differ from %s" % (nm, bad[nm], count, names[0]))
        if nm in first:
            doc, want, got = first[nm]
            print("   first:", " | ".join(doc))
            for a, b in zip(want, got):
                if a != b:
                    print("   want", a)
                    print("   got ", b)
                    break
            else:
                print("   lengths", len(want), len(got))
    return 1 if any(bad.values()) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
