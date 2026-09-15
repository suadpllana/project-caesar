"""The generated population, built inside the verifier from a seed drawn after the agent's
container is gone.

Ten families, each shaped around a decision rather than drawn at random: an unshaped
population exercises the ordinary path and leaves the mechanism alone. `press` keeps the
pool short enough that a take-back lands while its holder is still running, which is what
strands a request's own tail; `again` asks for the same prompt afterwards, which is where
the shortened walk shows; `twin` makes two requests emit the same tokens after the same
prompt so a completed page meets its own content; `stall` sets a budget that cannot always
reach the next page boundary; `kick` makes the pool too small for what is resident. `wide`
and `deep` are the two scale families and carry the execution limit.
"""
import random

FAMILIES = (
    ("plain", False),
    ("share", False),
    ("press", False),
    ("again", False),
    ("stall", False),
    ("kick", False),
    ("twin", False),
    ("cut", False),
    ("long", False),
    ("mix", False),
    ("wide", True),
    ("deep", True),
)

SHAPE = {
    "plain": dict(pool=(10, 26), w=(2, 8), pages=(1, 4), reqs=(2, 5), tight=0),
    "share": dict(pool=(12, 30), w=(2, 6), pages=(2, 5), reqs=(4, 8), tight=0),
    "press": dict(pool=(5, 9), w=(2, 4), pages=(2, 4), reqs=(3, 6), tight=2),
    "again": dict(pool=(5, 10), w=(2, 4), pages=(2, 5), reqs=(4, 8), tight=2),
    "stall": dict(pool=(10, 20), w=(4, 8), pages=(2, 4), reqs=(3, 6), tight=1),
    "kick": dict(pool=(3, 6), w=(2, 4), pages=(2, 4), reqs=(2, 4), tight=3),
    "twin": dict(pool=(8, 18), w=(2, 4), pages=(1, 3), reqs=(4, 8), tight=0),
    "cut": dict(pool=(6, 14), w=(2, 4), pages=(1, 4), reqs=(4, 8), tight=1),
    "long": dict(pool=(10, 22), w=(2, 4), pages=(4, 9), reqs=(2, 4), tight=1),
    "mix": dict(pool=(5, 14), w=(2, 5), pages=(1, 6), reqs=(4, 9), tight=2),
}


def segs(toks):
    out = []
    for tok in toks:
        if out and out[-1][1] == tok:
            out[-1][0] += 1
        else:
            out.append([1, tok])
    return ",".join("%d:%d" % (c, t) for c, t in out) if out else "-"


def chains(rng, fam, w, pages):
    """Prompt bodies that share prefixes, so a walk has something to reach."""
    deep = pages[1] * w + w
    trunk = [rng.randint(1, 3) for _ in range(deep)]
    out = [trunk]
    for _ in range(2):
        cut = rng.randrange(w, deep + 1)
        out.append(trunk[:cut] + [rng.randint(4, 6) for _ in range(deep - cut)])
    if fam == "twin":
        out = [trunk]
    return out


def body(rng, fam, sh, w, pool):
    """One program: a pool line, then requests and steps interleaved."""
    sink = rng.choice([0, w, w + 1, 2 * w])
    win = rng.choice([1, w, 2 * w - 1, 2 * w, 3 * w])
    bud = {0: rng.choice([4 * w, 6 * w]), 1: rng.choice([w, w + 1, 2 * w - 1]),
           2: rng.choice([2 * w, 3 * w]), 3: rng.choice([2 * w, 4 * w])}[sh["tight"]]
    lines = ["pool %d %d %d %d %d" % (pool, w, sink, win, bud)]
    pool_names = []
    trunks = chains(rng, fam, w, sh["pages"])
    reqs = rng.randint(*sh["reqs"])
    early = []
    for i in range(reqs):
        name = "r%d" % i
        trunk = trunks[i % len(trunks)]
        take = rng.randint(sh["pages"][0] * w, min(len(trunk), sh["pages"][1] * w))
        if fam == "twin":
            ask = trunk[:take]
            out = [7] * rng.randint(w, 2 * w)
        elif fam == "share":
            ask = trunk[:take]
            out = [rng.randint(7, 9) for _ in range(rng.randint(1, 2 * w))]
        else:
            ask = trunk[:take] + [rng.randint(10 + i, 12 + i)] * rng.randint(0, w)
            out = [rng.randint(7, 9) for _ in range(rng.randint(1, 2 * w))]
        early.append((name, ask, out))
        pool_names.append(name)
    order = list(range(reqs))
    if fam == "again":
        for i in range(2):
            name = "q%d" % i
            early.append((name, early[i][1], early[i][2]))
            pool_names.append(name)
            order.append(len(early) - 1)
    span = {nm: len(a) + len(o) for nm, a, o in early}
    seen = []
    rounds = rng.randint(6, 14)
    for _ in range(rounds):
        for _ in range(rng.randint(0, 2)):
            if not order:
                break
            name, ask, out = early[order.pop(0)]
            seen.append(name)
            lines.append("ask %s %s %s" % (name, segs(ask), segs(out)))
        for _ in range(rng.randint(1, 3)):
            lines.append("step")
        if seen and rng.random() < 0.4:
            who = rng.choice(seen)
            lines.append("at %s %d" % (who, rng.randrange(span[who])))
        if fam == "cut" and seen and rng.random() < 0.25:
            lines.append("stop %s" % rng.choice(seen))
    while order:
        name, ask, out = early[order.pop(0)]
        seen.append(name)
        lines.append("ask %s %s %s" % (name, segs(ask), segs(out)))
    lines.extend(["step"] * rng.randint(3, 8))
    for _ in range(rng.randint(3, 6)):
        who = rng.choice(seen)
        lines.append("at %s %d" % (who, rng.randrange(span[who])))
    return lines


def wide(rng):
    """A pool with no free page left, and a take-back for every page handed out after that.

    Every request here holds one page of its own, so nothing is reused, nothing cascades, and
    once the requests that have finished have filled the pool each new page costs a take-back.
    That is where the age order over the reusable pages, and the reach of a take-back, are
    read tens of thousands of times.
    """
    many = rng.randint(99000, 101000)
    lines = ["pool 50000 16 32 512 6144"]
    lines.append("bulk a %d - 12 4" % many)
    lines.extend(["step"] * 620)
    for i in range(0, many, 24000):
        lines.append("at a%d 4" % i)
    return lines


def deep(rng):
    """One prompt of thousands of pages, shared, with the window moving over all of it.

    Residency is the first two pages and the last thirty-two, so every decoded token moves
    the window against a request that holds thousands of pages, and what falls out is a
    page in the middle of a chain that is still being read from both ends.
    """
    run = rng.randint(8900, 9100)
    lines = ["pool 12000 16 32 512 8192"]
    lines.append("bulk d 6 %s 32 24000" % segs([3] * (run * 16)))
    lines.extend(["step"] * 24600)
    for i in range(5):
        lines.append("at d%d %d" % (i, run * 16 - 8))
    return lines


def programs(seed, per):
    out = []
    for fam, big in FAMILIES:
        if big:
            continue
        for i in range(per):
            rng = random.Random("%s/%s/%d" % (seed, fam, i))
            sh = SHAPE[fam]
            w = rng.randint(*sh["w"])
            pool = rng.randint(*sh["pool"])
            out.append((fam, "%s-%d" % (fam, i), body(rng, fam, sh, w, pool)))
    for fam, maker in (("wide", wide), ("deep", deep)):
        for i in range(3):
            out.append((fam, "%s-%d" % (fam, i), maker(random.Random("%s/%s/%d" % (seed, fam, i)))))
    return out
