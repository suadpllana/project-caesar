"""The nonce population, generated inside the verifier from a seed drawn after the agent's
container is gone.

Eleven families, each shaped at a decision point rather than sampled uniformly. An unshaped
population barely exercises this service: most requests on a wide namespace are compatible,
so a run of random programs would almost never make a holder give way, never narrow a cover
and never cross the widen threshold. Every family below deliberately presses on one thing.

  plain  compatible traffic only - the side of the fence an overcautious service fails
  clash  keys two transactions both want, so somebody gives way on nearly every line
  cover  explicit takes at block and store level mixed with keys, then drops, so the
         difference between an asked mode and a derived cover decides most lines
  deep   holders with a subtree under them, struck at the block or the store, so the
         cascade and the narrowing that follows it run constantly
  park   claims left blocked at one level while other levels of the same chain move
  race   three ages and a claim that outlives the transaction that caused it, so retakes
         preempt holders that arrived long afterwards
  edge   modes chosen from the pairs where the lattice is not the obvious one
  grow   thresholds low enough that widening fires at both levels, and grants that come and
         go so the count crosses the line in both directions
  hold   the no-look-ahead shape: a younger holder above, an older holder below
  wide   the first scale family: one block holding thousands of keys
  busy   the second scale family: hundreds of transactions, a contended handful of blocks
         nobody can enter, and long traffic somewhere else

`programs(seed, per)` returns (family, name, lines) for every program. The two scale families
have a fixed small count because each one is large.
"""
import random

MODES = ("IS", "IX", "S", "SIX", "X")
READ = ("IS", "S")
WRITE = ("IX", "SIX", "X")

FAMILIES = (
    ("plain", False),
    ("clash", False),
    ("cover", False),
    ("deep", False),
    ("park", False),
    ("race", False),
    ("edge", False),
    ("grow", False),
    ("hold", False),
    ("wide", True),
    ("busy", True),
)

BIG_EACH = 5


def _res(rng, blocks, keys, store=0):
    pick = rng.random()
    if pick < 0.08:
        return "s%d" % store
    if pick < 0.28:
        return "s%d.b%d" % (store, rng.randrange(blocks))
    return "s%d.b%d.k%d" % (store, rng.randrange(blocks), rng.randrange(keys))


def _head(names, lim):
    return ["lim %d" % lim] + ["open %s" % n for n in names]


def plain(rng):
    """Nobody ever conflicts: every transaction owns its own block, and modes are shared."""
    n = rng.randrange(2, 5)
    names = ["t%d" % i for i in range(n)]
    rows = _head(names, rng.randrange(4, 9))
    for _ in range(rng.randrange(10, 26)):
        i = rng.randrange(n)
        t = names[i]
        r = rng.random()
        if r < 0.72:
            rows.append("take %s s0.b%d.k%d %s"
                        % (t, i, rng.randrange(6), rng.choice(READ if rng.random() < 0.5
                                                              else WRITE)))
        elif r < 0.86:
            rows.append("take %s s0.b%d %s" % (t, i, rng.choice(("IS", "IX"))))
        else:
            rows.append("drop %s s0.b%d.k%d" % (t, i, rng.randrange(6)))
    return rows


def clash(rng):
    """Two or three transactions over two keys: a give-up on most lines."""
    n = rng.randrange(2, 4)
    names = ["t%d" % i for i in range(n)]
    rows = _head(names, rng.randrange(4, 9))
    for _ in range(rng.randrange(12, 30)):
        t = rng.choice(names)
        r = rng.random()
        if r < 0.78:
            rows.append("take %s s0.b0.k%d %s" % (t, rng.randrange(2), rng.choice(MODES)))
        elif r < 0.9:
            rows.append("drop %s s0.b0.k%d" % (t, rng.randrange(2)))
        else:
            rows.append("shut %s" % t)
            rows.append("open %s" % t)
    return rows


def cover(rng):
    """Asked modes and derived covers on the same nodes, then drops that make covers fall."""
    n = rng.randrange(2, 5)
    names = ["t%d" % i for i in range(n)]
    rows = _head(names, rng.randrange(5, 10))
    for _ in range(rng.randrange(14, 32)):
        t = rng.choice(names)
        r = rng.random()
        if r < 0.34:
            rows.append("take %s s0.b%d %s" % (t, rng.randrange(3), rng.choice(MODES)))
        elif r < 0.44:
            rows.append("take %s s0 %s" % (t, rng.choice(("IS", "IX"))))
        elif r < 0.78:
            rows.append("take %s s0.b%d.k%d %s"
                        % (t, rng.randrange(3), rng.randrange(4), rng.choice(MODES)))
        else:
            rows.append("drop %s s0.b%d.k%d" % (t, rng.randrange(3), rng.randrange(4)))
    return rows


def deep(rng):
    """Holders with subtrees, struck at the block or the store."""
    n = rng.randrange(3, 6)
    names = ["t%d" % i for i in range(n)]
    rows = _head(names, rng.randrange(5, 10))
    for t in names:
        for b in range(2):
            rows.append("take %s s0.b%d.k%d %s"
                        % (t, b, rng.randrange(3), rng.choice(MODES)))
    for _ in range(rng.randrange(10, 26)):
        t = rng.choice(names)
        r = rng.random()
        if r < 0.45:
            rows.append("take %s s0.b%d %s" % (t, rng.randrange(2), rng.choice(("S", "X"))))
        elif r < 0.6:
            rows.append("take %s s0 %s" % (t, rng.choice(("S", "X"))))
        elif r < 0.85:
            rows.append("take %s s0.b%d.k%d %s"
                        % (t, rng.randrange(2), rng.randrange(3), rng.choice(MODES)))
        else:
            rows.append("drop %s s0.b%d" % (t, rng.randrange(2)))
    return rows


def park(rng):
    """Claims stuck at one level while the levels around them keep moving."""
    n = rng.randrange(3, 6)
    names = ["t%d" % i for i in range(n)]
    rows = _head(names, rng.randrange(5, 10))
    rows.append("take t0 s0.b0.k0 %s" % rng.choice(("S", "X")))
    for t in names[1:]:
        rows.append("take %s s0.b0.k0 %s" % (t, rng.choice(("S", "X"))))
    for _ in range(rng.randrange(12, 30)):
        t = rng.choice(names)
        r = rng.random()
        if r < 0.5:
            rows.append("take %s s0.b%d.k%d %s"
                        % (t, rng.randrange(1, 4), rng.randrange(4), rng.choice(MODES)))
        elif r < 0.66:
            rows.append("take %s s0.b%d %s" % (t, rng.randrange(1, 4), rng.choice(MODES)))
        elif r < 0.84:
            rows.append("drop %s s0.b%d" % (t, rng.randrange(1, 4)))
        else:
            rows.append("take %s s0.b0.k0 %s" % (t, rng.choice(MODES)))
    return rows


def race(rng):
    """A claim left early that comes back after holders that never met its owner."""
    names = ["t%d" % i for i in range(rng.randrange(4, 7))]
    rows = _head(names, rng.randrange(5, 10))
    rows.append("take %s s0 %s" % (names[1], rng.choice(("S", "X"))))
    rows.append("take %s s0.b0.k1 %s" % (names[0], rng.choice(("X", "SIX"))))
    for t in names[2:]:
        rows.append("take %s s0.b%d.k%d %s"
                    % (t, rng.randrange(1, 3), rng.randrange(3), rng.choice(MODES)))
    for _ in range(rng.randrange(10, 24)):
        t = rng.choice(names)
        r = rng.random()
        if r < 0.4:
            rows.append("take %s s0.b%d.k%d %s"
                        % (t, rng.randrange(3), rng.randrange(3), rng.choice(MODES)))
        elif r < 0.56:
            rows.append("take %s s0 %s" % (t, rng.choice(MODES)))
        elif r < 0.76:
            rows.append("drop %s s0.b%d" % (t, rng.randrange(3)))
        else:
            rows.append("shut %s" % t)
            rows.append("open %s" % t)
    return rows


def edge(rng):
    """Modes drawn from the pairs where the lattice or the cover is not the obvious one."""
    n = rng.randrange(2, 5)
    names = ["t%d" % i for i in range(n)]
    rows = _head(names, rng.randrange(5, 10))
    sharp = ("IX", "S", "SIX")
    for _ in range(rng.randrange(12, 28)):
        t = rng.choice(names)
        r = rng.random()
        if r < 0.4:
            rows.append("take %s s0.b%d %s" % (t, rng.randrange(2), rng.choice(sharp)))
        elif r < 0.8:
            rows.append("take %s s0.b%d.k%d %s"
                        % (t, rng.randrange(2), rng.randrange(3), rng.choice(sharp + ("X",))))
        else:
            rows.append("drop %s s0.b%d.k%d" % (t, rng.randrange(2), rng.randrange(3)))
    return rows


def grow(rng):
    """A low threshold, at both levels, with grants that come and go."""
    n = rng.randrange(2, 5)
    names = ["t%d" % i for i in range(n)]
    rows = _head(names, rng.randrange(1, 4))
    for _ in range(rng.randrange(14, 32)):
        t = rng.choice(names)
        r = rng.random()
        if r < 0.66:
            rows.append("take %s s0.b%d.k%d %s"
                        % (t, rng.randrange(3), rng.randrange(5), rng.choice(MODES)))
        elif r < 0.78:
            rows.append("take %s s0.b%d %s" % (t, rng.randrange(3), rng.choice(("IS", "IX"))))
        elif r < 0.92:
            rows.append("drop %s s0.b%d.k%d" % (t, rng.randrange(3), rng.randrange(5)))
        else:
            rows.append("drop %s s0.b%d" % (t, rng.randrange(3)))
    return rows


def hold(rng):
    """A younger holder above and an older holder below, so a refusal still costs somebody."""
    names = ["t%d" % i for i in range(rng.randrange(3, 6))]
    rows = _head(names, rng.randrange(5, 10))
    rows.append("take %s s0.b0.k0 S" % names[0])
    rows.append("take %s s0.b0 S" % names[-1])
    for _ in range(rng.randrange(12, 28)):
        t = rng.choice(names)
        r = rng.random()
        if r < 0.44:
            rows.append("take %s s0.b0.k%d %s" % (t, rng.randrange(3), rng.choice(MODES)))
        elif r < 0.62:
            rows.append("take %s s0.b%d %s" % (t, rng.randrange(2), rng.choice(("S", "IS"))))
        elif r < 0.76:
            rows.append("take %s s0 %s" % (t, rng.choice(("IS", "S"))))
        elif r < 0.9:
            rows.append("drop %s s0.b%d.k%d" % (t, rng.randrange(2), rng.randrange(3)))
        else:
            rows.append("drop %s s0.b%d" % (t, rng.randrange(2)))
    return rows


def wide(rng):
    """One block holding thousands of keys: the cover above it must not be rescanned."""
    keys = rng.randrange(26000, 32000)
    cap = rng.randrange(8000, 9600)
    rows = ["lim 9000", "open t0", "open t1", "open t2"]
    live = {"t0": [], "t1": [], "t2": []}
    for _ in range(rng.randrange(18000, 21000)):
        t = rng.choice(("t0", "t1", "t2"))
        if len(live[t]) > cap and rng.random() < 0.42:
            k = live[t].pop(rng.randrange(len(live[t])))
            rows.append("drop %s %s" % (t, k))
        else:
            k = "s0.b0.k%d" % rng.randrange(keys)
            live[t].append(k)
            rows.append("take %s %s %s" % (t, k, rng.choice(READ)))
    return rows


def busy(rng):
    """Hundreds of transactions, a contended core nobody can enter, and traffic elsewhere."""
    txns = rng.randrange(340, 420)
    core = rng.randrange(8, 13)
    rest = rng.randrange(130, 170)
    keys = rng.randrange(80, 100)
    rows = ["lim 6", "open g0", "open g1"]
    for i in range(core):
        rows.append("take %s s0.b%d X" % ("g0" if i % 2 == 0 else "g1", i))
    names = ["t%d" % i for i in range(txns)]
    for n in names:
        rows.append("open %s" % n)
    for n in names:
        rows.append("take %s s0.b%d.k%d IS" % (n, core + rng.randrange(rest),
                                               rng.randrange(keys)))
        for _ in range(rng.randrange(26, 34)):
            rows.append("take %s s0.b%d.k%d %s" % (n, rng.randrange(core),
                                                   rng.randrange(keys),
                                                   rng.choice(("S", "X"))))
    for _ in range(rng.randrange(12000, 14000)):
        t = rng.choice(names)
        b = core + rng.randrange(rest)
        r = rng.random()
        if r < 0.74:
            rows.append("take %s s0.b%d.k%d %s" % (t, b, rng.randrange(keys),
                                                   rng.choice(("IS", "IS", "IX", "S", "X"))))
        elif r < 0.84:
            rows.append("take %s s0.b%d %s" % (t, b, rng.choice(("IS", "IX", "S"))))
        else:
            rows.append("drop %s s0.b%d" % (t, b))
    return rows


MAKE = {
    "plain": plain,
    "clash": clash,
    "cover": cover,
    "deep": deep,
    "park": park,
    "race": race,
    "edge": edge,
    "grow": grow,
    "hold": hold,
    "wide": wide,
    "busy": busy,
}


def programs(seed, per):
    """(family, name, lines) for the whole nonce population."""
    out = []
    for fam, big in FAMILIES:
        count = BIG_EACH if big else per
        for i in range(count):
            rng = random.Random("%s/%s/%d" % (seed, fam, i))
            out.append((fam, "%s-%04d" % (fam, i), MAKE[fam](rng)))
    return out
