"""Program generation for the graded set.

Ten families, each shaped around one part of the contract rather than drawn at random:
programs that never reach a cycle, programs built to reach one, programs that stack and
pop claims, programs that queue fresh claims behind a blocked one, programs that leave a
raise stuck so the pin rule decides, programs that chain waits across several items, one
item shared by a crowd of compatible holders, and long programs over many items.

Every program is well formed by construction: inside one transaction's own steps, a drop
is always preceded by an unmatched take of that item, so the trace never depends on how a
malformed step would be treated.
"""

import random

MARKS = ("scan", "edit", "grow", "pin", "seal")
SOFT = ("scan", "grow", "pin")


def _weave(rng, parts):
    """Interleave per-transaction step lists, keeping each transaction's own order."""
    parts = [list(p) for p in parts if p]
    out = []
    while parts:
        i = rng.randrange(len(parts))
        out.append(parts[i].pop(0))
        if not parts[i]:
            parts.pop(i)
    return out


def _thread(rng, tn, keys, moves, marks=MARKS, close=True):
    """One transaction's steps: takes, raises, drops, and an end."""
    steps = []
    depth = {}
    for _ in range(moves):
        pick = rng.random()
        held = [k for k, d in depth.items() if d > 0]
        if held and pick < 0.3:
            k = rng.choice(held)
            steps.append(("drop", tn, k))
            depth[k] -= 1
        elif held and pick < 0.6:
            k = rng.choice(held)
            steps.append(("take", tn, k, rng.choice(marks)))
            depth[k] += 1
        else:
            k = rng.choice(keys)
            steps.append(("take", tn, k, rng.choice(marks)))
            depth[k] = depth.get(k, 0) + 1
    if close:
        steps.append(("end", tn))
    return steps


def plain(rng, n=6, keys=6, moves=6):
    ks = ["k%d" % i for i in range(keys)]
    return _weave(rng, [_thread(rng, "t%d" % i, ks, moves, SOFT) for i in range(1, n + 1)])


def lift(rng, n=5, keys=3, moves=8):
    ks = ["k%d" % i for i in range(keys)]
    parts = []
    for i in range(1, n + 1):
        tn = "t%d" % i
        steps = [("take", tn, rng.choice(ks), rng.choice(SOFT))]
        held = [steps[0][2]]
        for _ in range(moves):
            k = rng.choice(held) if rng.random() < 0.75 else rng.choice(ks)
            steps.append(("take", tn, k, rng.choice(MARKS)))
            held.append(k)
        steps.append(("end", tn))
        parts.append(steps)
    return _weave(rng, parts)


def knot(rng, n=4, keys=2, moves=3):
    """Transactions that share items and then raise on them: cycles by construction."""
    ks = ["k%d" % i for i in range(keys)]
    parts = []
    for i in range(1, n + 1):
        tn = "t%d" % i
        mine = rng.sample(ks, rng.randint(1, len(ks)))
        steps = [("take", tn, k, rng.choice(SOFT)) for k in mine]
        for _ in range(moves):
            steps.append(("take", tn, rng.choice(mine), rng.choice(MARKS)))
        steps.append(("end", tn))
        parts.append(steps)
    return _weave(rng, parts)


def stackup(rng, n=4, keys=3, deep=5):
    ks = ["k%d" % i for i in range(keys)]
    parts = []
    for i in range(1, n + 1):
        tn = "t%d" % i
        steps = []
        depth = {}
        for _ in range(deep * 2):
            held = [k for k, d in depth.items() if d > 0]
            if held and rng.random() < 0.45:
                k = rng.choice(held)
                steps.append(("drop", tn, k))
                depth[k] -= 1
            else:
                k = rng.choice(ks)
                steps.append(("take", tn, k, rng.choice(MARKS)))
                depth[k] = depth.get(k, 0) + 1
        steps.append(("end", tn))
        parts.append(steps)
    return _weave(rng, parts)


def queue(rng, n=7, keys=2):
    """A hard mark first, then a crowd of fresh claims lining up behind it."""
    ks = ["k%d" % i for i in range(keys)]
    parts = [[("take", "t1", k, "seal") for k in ks] + [("end", "t1")]]
    for i in range(2, n + 1):
        tn = "t%d" % i
        steps = []
        for k in rng.sample(ks, rng.randint(1, len(ks))):
            steps.append(("take", tn, k, rng.choice(MARKS)))
        steps.append(("end", tn))
        parts.append(steps)
    return _weave(rng, parts)


def pinned(rng, n=5, keys=2):
    """Holders in compatible marks, one of them raising into a conflict, then fresh
    claims that the pin stops even though nothing they conflict with is held."""
    ks = ["k%d" % i for i in range(keys)]
    parts = []
    base = rng.sample(range(1, n + 1), max(2, n // 2))
    for i in range(1, n + 1):
        tn = "t%d" % i
        steps = []
        if i in base:
            for k in ks:
                steps.append(("take", tn, k, rng.choice(("scan", "pin"))))
            steps.append(("take", tn, rng.choice(ks), rng.choice(("pin", "grow", "edit"))))
        else:
            steps.append(("take", tn, rng.choice(ks), "scan"))
        steps.append(("end", tn))
        parts.append(steps)
    return _weave(rng, parts)


def chain(rng, n=5, keys=4):
    """Each transaction holds one item and reaches for the next one along, so waits run
    in a ring through queue positions as well as through claims."""
    ks = ["k%d" % i for i in range(keys)]
    parts = []
    for i in range(1, n + 1):
        tn = "t%d" % i
        a = ks[i % keys]
        b = ks[(i + 1) % keys]
        steps = [("take", tn, a, rng.choice(SOFT)),
                 ("take", tn, b, rng.choice(("edit", "seal", "grow"))),
                 ("take", tn, a, rng.choice(MARKS)),
                 ("end", tn)]
        parts.append(steps)
    return _weave(rng, parts)


def crowd(rng, holders=6000, waits=25, churn=1500):
    """One item carried by a crowd of holders in a mark they all share, one raise stuck
    across it, a queue of fresh claims the pin holds back, and a long run of raises by
    the crowd that moves the item under all of them."""
    out = []
    for i in range(1, holders + 1):
        out.append(("take", "t%d" % i, "k0", "scan"))
    out.append(("take", "t1", "k0", "pin"))
    for j in range(waits):
        out.append(("take", "t%d" % (holders + 1 + j), "k0", rng.choice(SOFT)))
    for _ in range(churn):
        out.append(("take", "t%d" % rng.randrange(2, holders + 1), "k0", "scan"))
    return out


def wide(rng, pairs=1000, others=500, moves=6):
    """Many items each holding one request that never goes through, and a long run of
    work on other items entirely."""
    out = []
    n = 0
    for i in range(pairs):
        n += 1
        a = "t%d" % n
        n += 1
        b = "t%d" % n
        k = "k%d" % i
        out.append(("take", a, k, "edit"))
        out.append(("take", b, k, "scan"))
    tail = []
    for j in range(others):
        n += 1
        tn = "t%d" % n
        mine = ["p%d-%d" % (j, m) for m in range(3)]
        steps = []
        for _ in range(moves):
            steps.append(("take", tn, rng.choice(mine), rng.choice(MARKS)))
        steps.append(("end", tn))
        tail.append(steps)
    out.extend(_weave(rng, tail))
    return out


def churn(rng, n=8, keys=3, moves=10):
    """Names that come back: items dropped to nothing and taken again, transactions that
    end and are named again afterwards."""
    ks = ["k%d" % i for i in range(keys)]
    parts = []
    for i in range(1, n + 1):
        tn = "t%d" % i
        steps = _thread(rng, tn, ks, moves, MARKS, close=True)
        if rng.random() < 0.5:
            steps.append(("take", tn, rng.choice(ks), rng.choice(MARKS)))
        parts.append(steps)
    return _weave(rng, parts)



def flip(rng, n=6, keys=2):
    """Two holders that come to hold an item in one order and raise on it in the other,
    with a blocker whose departure lets exactly one of the raises through."""
    ks = ["k%d" % i for i in range(keys)]
    parts = []
    hard = "t1"
    blocked = [("take", hard, k, "edit") for k in ks]
    for i in range(2, n + 1):
        tn = "t%d" % i
        k = rng.choice(ks)
        parts.append([("take", tn, k, "pin"), ("take", tn, k, rng.choice(("scan", "pin")))])
    rng.shuffle(parts)
    holds = _weave(rng, [[s] for p in parts for s in p[:1]])
    asks = _weave(rng, [[s] for p in parts for s in p[1:]])
    out = blocked + holds + asks
    for k in ks:
        out.append(("drop", hard, k))
    out.append(("end", hard))
    return out


def ring(rng, n=3, extra=2):
    """Several rings that all appear in one step, with the transactions on them holding
    different numbers of items so the cut has to compare across rings."""
    out = []
    pairs = []
    who = 2
    for r in range(n):
        a, b = "t%d" % who, "t%d" % (who + 1)
        who += 2
        kn = "r%d" % r
        out.append(("take", a, kn, "scan"))
        out.append(("take", b, kn, "scan"))
        for tn in (a, b):
            for j in range(rng.randint(0, extra)):
                out.append(("take", tn, "%s-%s-%d" % (kn, tn, j), "scan"))
        pairs.append((a, b, kn))
    out.append(("take", "t1", "gate", "seal"))
    tails = []
    for a, b, kn in pairs:
        for tn in (a, b):
            tails.append([("take", tn, "gate", "scan"), ("take", tn, kn, "edit")])
    rng.shuffle(tails)
    out.extend(_weave(rng, tails))
    out.append(("end", "t1"))
    return out

FAMILIES = ("plain", "lift", "knot", "stackup", "queue", "pinned", "chain",
            "churn", "flip", "ring")
HEAVY = ("crowd", "wide")


def make(kind, seed):
    rng = random.Random(seed)
    return globals()[kind](rng)


def programs(seed, per=None, heavy=None):
    """The graded population: `per` programs of each ordinary family and `heavy` of each
    large one, named by family and index."""
    per = 40 if per is None else per
    heavy = 6 if heavy is None else heavy
    out = []
    for kind in FAMILIES:
        for i in range(per):
            out.append(("%s-%d" % (kind, i), make(kind, "%s:%s:%d" % (kind, seed, i))))
    for kind in HEAVY:
        for i in range(heavy):
            out.append(("%s-%d" % (kind, i), make(kind, "%s:%s:%d" % (kind, seed, i))))
    return out


def text(steps):
    return "\n".join(" ".join(s) for s in steps) + "\n"
