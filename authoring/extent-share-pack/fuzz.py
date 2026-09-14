"""Random programs through the reference and the brute-force engine, compared line for line."""
import random
import sys

import brute
import harness

HERE = harness.HERE
SOL = harness.TASK / "solution"


def program(rng, ops=30, vols=3, fils=2, slots=8, siz=5):
    files = ["p", "q", "r"][:fils]
    nxt = [0]
    live = ["a"]
    out = ["vol a"] + ["fil a %s %d" % (f, slots) for f in files]
    made = {"a": set(files)}
    for _ in range(ops):
        pick = rng.random()
        v = rng.choice(live)
        if pick < 0.30:
            f = rng.choice(sorted(made[v]))
            lo = rng.randrange(slots)
            hi = min(slots - 1, lo + rng.randrange(siz))
            out.append("wr %s %s %d %d" % (v, f, lo, hi))
        elif pick < 0.45:
            f = rng.choice(sorted(made[v]))
            lo = rng.randrange(slots)
            hi = min(slots - 1, lo + rng.randrange(siz))
            out.append("tr %s %s %d %d" % (v, f, lo, hi))
        elif pick < 0.62:
            w = rng.choice(live)
            f = rng.choice(sorted(made[v]))
            g = rng.choice(sorted(made[w]))
            lo = rng.randrange(slots)
            hi = min(slots - 1, lo + rng.randrange(3))
            off = rng.randrange(slots - (hi - lo))
            out.append("cp %s %s %d %d %s %s %d" % (v, f, lo, hi, w, g, off))
        elif pick < 0.72 and len(live) < vols:
            nxt[0] += 1
            w = "s%d" % nxt[0]
            out.append("sn %s %s" % (v, w))
            made[w] = set(made[v])
            live.append(w)
        elif pick < 0.78 and len(live) > 1:
            w = rng.choice([x for x in live if x != "a"] or ["a"])
            if w != "a":
                out.append("rm %s" % w)
                live.remove(w)
        elif pick < 0.92:
            out.append(rng.choice(["use %s" % v, "own %s" % v, "tot"]))
        else:
            out.append("tot")
    out.append("tot")
    for v in live:
        out.append("use %s" % v)
        out.append("own %s" % v)
    return out


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    run = harness.runner(SOL)
    rng = random.Random(seed)
    bad = 0
    for k in range(n):
        lines = program(rng)
        want = brute.expect(lines)
        got = run(lines)
        if got != want:
            bad += 1
            print("MISMATCH program %d" % k, flush=True)
            for line in lines:
                print("   " + line)
            for i in range(max(len(got), len(want))):
                g = got[i] if i < len(got) else "-"
                w = want[i] if i < len(want) else "-"
                if g != w:
                    print("   line %d: reference %r brute %r" % (i, g, w))
            if bad >= 2:
                return 1
    print("%d programs, %d mismatches" % (n, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
