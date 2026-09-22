"""Search for the brief's worked example instead of choosing it (CLAUDE.md, reach-pair-sweep).

The brief prints one launch and its exact output so a format slip cannot fail every case for
a reason that is not the task. A printed answer is an oracle for every rule it decides, so the
example must decide none: every wrong reading in switches.py has to print the same lines as
the model on it. It must also show every kind of output line - a finished block with values,
a hang, a stuck block, the count left unplaced, and a memory word - and be as short as that
allows.

Usage: python3 authoring/stale-line-spin/example_search.py [tries] [seed]
"""
import random
import sys

sys.path.insert(0, "authoring/stale-line-spin")
import switches  # noqa: E402  (puts tests/ and tests/seal/ on the path)
import model  # noqa: E402

ADDRS = (0, 1, 4, 5)


def one(rng):
    S, R, C = rng.choice((1, 2)), 1, rng.choice((1, 2))
    G = S * R + rng.choice((0, 1, 2))
    shows = sorted(rng.sample(ADDRS, rng.choice((1, 2))))
    mem = [(a, rng.randint(1, 5)) for a in rng.sample(ADDRS, rng.choice((0, 1)))]

    def op():
        k = rng.random()
        a = rng.choice(ADDRS)
        r = rng.randint(0, 2)
        if k < 0.20:
            return "ld.%s r%d [%d]" % (rng.choice(("ca", "cg")), r, a)
        if k < 0.35:
            return "st [%d] %d" % (a, rng.randint(1, 3))
        if k < 0.45:
            return "atom.add r%d [%d] 1" % (r, a)
        if k < 0.55:
            return "work %d" % rng.randint(1, 4)
        if k < 0.70:
            return "out r%d" % r
        if k < 0.78:
            return "add r%d r%d %d" % (r, rng.randint(0, 2), rng.randint(1, 3))
        return "spin.%s r3 [%d] %s %d" % (rng.choice(("ca", "cg")), a,
                                          rng.choice(("eq", "ne", "ge")), rng.randint(0, 2))

    first = [op() for _ in range(rng.randint(1, 3))]
    other = [op() for _ in range(rng.randint(1, 3))]
    lines = ["dev %d %d %d" % (S, R, C), "grid %d" % G]
    lines += ["mem %d %d" % kv for kv in mem]
    lines += ["show " + " ".join(str(a) for a in shows), "prog", "brnz %bid rest"]
    lines += first + ["exit", "rest:"] + other + ["exit"]
    return lines


def good(out):
    kinds = {x.split()[0] for x in out}
    blk_vals = any(x.startswith("blk ") and len(x.split()) > 8 for x in out)
    left = [x for x in out if x.startswith("left ")]
    return (kinds >= {"blk", "hang", "spin", "left", "mem"} and blk_vals
            and left and left[0] != "left 0")


# Measured on 60,000 candidates: every one that shows each kind of line decides at least these
# four readings of switches.py, because each dates something the example has to print - a
# block placed after an exit, a first issue, a hang. They are the stated timing rules the
# example exists to show; the cache, residency and skipping readings must stay undecided.
FLOOR = {"free-same-cycle", "placed-next-cycle", "park-spinners", "hang-at-detect"}


def features(lines, want):
    """Prefer an example that shows more of the format: values on a stuck block, a memory word
    that is not zero, two multiprocessors, a write."""
    return (any(x.startswith("spin ") and len(x.split()) > 8 for x in want)
            + any(x.startswith("mem ") and x.split()[2] != "0" for x in want)
            + (lines[0].split()[1] == "2")
            + any(ln.startswith(("st ", "atom")) for ln in lines))


def main():
    tries = int(sys.argv[1]) if len(sys.argv) > 1 else 60000
    rng = random.Random(sys.argv[2] if len(sys.argv) > 2 else "example")
    keep = []
    for _ in range(tries):
        lines = one(rng)
        try:
            want = model.expect(lines)
        except Exception:
            continue
        if not good(want):
            continue
        if switches.run(lines) != want:
            raise SystemExit("switchless stepper disagrees with the model:\n" + "\n".join(lines))
        dec = {rd for rd in switches.SWITCHES if switches.run(lines, frozenset([rd])) != want}
        if dec <= FLOOR:
            keep.append((-features(lines, want), len(lines), lines, want))
    keep.sort(key=lambda k: (k[0], k[1], k[2]))
    print("%d candidates decide nothing beyond the floor" % len(keep))
    for f, n, lines, want in keep[:3]:
        print("--- features %d, %d lines" % (-f, n))
        print("\n".join(lines))
        print("=>")
        print("\n".join(want))


if __name__ == "__main__":
    main()
