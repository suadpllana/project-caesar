"""Differential fuzz of the sealed model against the plain stepper on launches with sums.

Unshaped on purpose, unlike tests/gen.py: every block gets its own short program from a pool
of role fragments (prefetch, sum, spin, store, atomic, fence, work), over a dozen lines, so
that stale copies, fills that push out a spinner's line, bypassing sums that drop one, and
stores racing a sum all turn up by chance. Also run with each plan mode, since a plan that is
wrong only when another multiprocessor is busy would hide behind "local".

usage: python3 authoring/stale-line-spin/fuzz_sums.py [count] [first-seed] [mode ...]
"""
import random
import sys
import time

sys.path.insert(0, "tasks/stale-line-spin/tests/seal")
sys.path.insert(0, "authoring/stale-line-spin")
import model  # noqa: E402
import naive  # noqa: E402

LINES = 12


def fragment(rng, lines):
    """A few instructions of one role, using r3..r7 freely and r1 = %bid."""
    k = rng.random()
    word = lambda: 4 * rng.choice(lines) + rng.randint(0, 3)  # noqa: E731
    out = []
    if k < 0.30:
        lo = rng.choice(lines)
        n = rng.randint(1, 8)
        op = rng.choice(("sum.ca", "sum.ca", "sum.cg"))
        if rng.random() < 0.3:
            out += ["mul r3 r1 %d" % rng.randint(0, 2), "%s r4 [r3+%d] %d" % (op, 4 * lo + rng.randint(0, 3), n)]
        else:
            out.append("%s r4 [%d] %d" % (op, 4 * lo + rng.randint(0, 3), n))
        out.append("out r4")
    elif k < 0.42:
        out += ["%s r5 [%d]" % (rng.choice(("ld.ca", "ld.ca", "ld.cg")), word()), "out r5"]
    elif k < 0.56:
        out.append("st [%d] %s" % (word(), rng.choice(("r1", "r4", str(rng.randint(1, 9))))))
    elif k < 0.62:
        out.append("atom.add r6 [%d] %d" % (word(), rng.randint(1, 3)))
    elif k < 0.67:
        out.append("fence")
    elif k < 0.82:
        out.append("work %d" % rng.randint(1, 25))
    else:
        a = word()
        op = rng.choice(("spin.ca", "spin.cg"))
        cmp = rng.choice(("ge", "eq", "ne", "lt"))
        v = rng.randint(0, 3)
        out += ["%s r7 [%d] %s %d" % (op, a, cmp, v), "out r7"]
    return out


def launch(seed):
    rng = random.Random(seed)
    S, R, C = rng.randint(1, 3), rng.randint(1, 4), rng.randint(1, 5)
    G = rng.randint(2, 8)
    lines = rng.sample(range(0, LINES), rng.randint(3, 8))
    mem = []
    for ln in lines:
        for w in range(4):
            if rng.random() < 0.5:
                mem.append((4 * ln + w, rng.randint(0, 5)))
    roles = rng.randint(1, min(G, 4))
    head = ["dev %d %d %d" % (S, R, C), "grid %d" % G]
    head += ["mem %d %d" % mw for mw in mem]
    show = sorted(rng.sample([4 * ln + w for ln in lines for w in range(4)], 4))
    head.append("show " + " ".join(map(str, show)))
    body = ["prog", "mov r1 %bid", "mod r2 r1 %d" % roles]
    for i in range(1, roles):
        body += ["sub r3 r2 %d" % i, "brz r3 role%d" % i]
    for i in range(roles):
        body.append("role%d:" % i)
        for _ in range(rng.randint(2, 6)):
            body += fragment(rng, lines)
        body.append("exit")
    return head + body


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    first = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    modes = sys.argv[3:] or ["local"]
    bad = 0
    hangs = 0
    t0 = time.time()
    for i in range(first, first + count):
        lines = launch(i)
        want = naive.run(lines)
        hangs += any(x.startswith("hang") for x in want)
        for mode in modes:
            got = model.expect(lines, mode)
            if got != want:
                bad += 1
                if bad <= 3:
                    print("DIFFER seed", i, "mode", mode)
                    print("\n".join(lines))
                    for a, b in zip(got, want):
                        if a != b:
                            print("   model:", a, "| naive:", b)
                    if len(got) != len(want):
                        print("   lengths", len(got), len(want))
    print("%d launches x %d modes, %d hang, %d disagreements, %.1fs" % (
        count, len(modes), hangs, bad, time.time() - t0))


if __name__ == "__main__":
    main()
