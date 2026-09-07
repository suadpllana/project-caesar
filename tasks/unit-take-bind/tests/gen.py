"""Programs generated inside the verifier from a nonce drawn after the agent has finished.

Seven families, each shaped around one part of the rule set rather than sampled uniformly:
a uniform program almost never puts two different origins at the same rank, and a rule that
is never exercised is a rule that is never graded.

  plain  chains and trees of wide pulls; the everyday side of every fence
  race   two origins deliberately placed at equal rank, so clashes are common
  near   the same name reachable at two different ranks, with the longer route declared first
  alias  `als` sources, so a pull's cost turns on the source reading's rank as well
  veil   `shut` and `hide` on names that other units pull both ways
  ring   pull cycles, including cycles that carry a clash
  wide   larger programs, deep chains and many names at once

Declaration order is shuffled in every family. The rules do not mention order anywhere, so a
settlement that depends on it is wrong, and shuffling is what makes that observable.
"""
import random

FAMILIES = (
    ("plain", 44),
    ("race", 48),
    ("near", 44),
    ("alias", 46),
    ("veil", 42),
    ("ring", 40),
    ("late", 44),
    ("wide", 10),
)

SHAPES = {
    #        units names own pull  wide   als  tagsrc  shut  hide asks depth
    "plain": (7, 4, 2, 2, 0.75, 0.00, 0.00, 0.00, 0.00, 5, 3),
    "race": (8, 3, 2, 3, 0.60, 0.10, 0.10, 0.05, 0.05, 6, 3),
    "near": (9, 3, 2, 3, 0.55, 0.10, 0.10, 0.05, 0.05, 6, 4),
    "alias": (9, 3, 2, 3, 0.50, 0.70, 0.55, 0.05, 0.05, 7, 4),
    "veil": (8, 4, 3, 3, 0.60, 0.15, 0.10, 0.35, 0.30, 6, 3),
    "ring": (7, 3, 2, 3, 0.60, 0.15, 0.15, 0.10, 0.10, 6, 3),
    "wide": (26, 6, 3, 4, 0.65, 0.30, 0.25, 0.15, 0.15, 22, 9),
}

TAGS = ("a0", "a1")


def _units(count):
    return ["u%d" % i for i in range(count)]


def _names(count):
    return ["n%d" % i for i in range(count)]


def _layered(rng, units, depth):
    """Split the units into layers; pulls run from a later layer to an earlier one."""
    order = list(units)
    rng.shuffle(order)
    layers = [[] for _ in range(depth)]
    base = max(1, len(order) // depth)
    for i, nm in enumerate(order):
        if i < base:
            layers[0].append(nm)
        else:
            layers[rng.randrange(1, depth)].append(nm)
    return [lay for lay in layers if lay]


def build(fam, rng):
    if fam == "late":
        return _late(rng)
    (nu, nn, nown, npull, wide, palias, ptag, pshut, phide, nask, depth) = SHAPES[fam]
    units = _units(nu)
    names = _names(nn)
    layers = _layered(rng, units, depth)
    at = {}
    for idx, lay in enumerate(layers):
        for nm in lay:
            at[nm] = idx

    lines = []
    for u in units:
        for _ in range(rng.randint(1, nown)):
            lines.append("%s own %s" % (u, rng.choice(names)))

    # An alias tag is usually a name of its own, but sometimes it collides with a unit name or
    # with an item name, which is what puts two readings of one source name, or an item and a
    # unit, at the same rank.
    for u in units:
        if rng.random() < palias:
            roll = rng.random()
            if roll < 0.55:
                tag = rng.choice(TAGS)
            elif roll < 0.8:
                tag = rng.choice(units)
            else:
                tag = rng.choice(names)
            lines.append("%s als %s %s" % (u, tag, rng.choice(units)))

    for u in units:
        lvl = at[u]
        for _ in range(rng.randint(1, npull)):
            if rng.random() < ptag:
                src = rng.choice(TAGS)
            elif fam == "ring" and rng.random() < 0.45:
                src = rng.choice(units)
            elif lvl == 0:
                src = rng.choice(units)
            else:
                lower = [v for v in units if at[v] < lvl]
                src = rng.choice(lower or units)
            if src == u:
                continue
            what = "*" if rng.random() < wide else rng.choice(names)
            lines.append("%s pull %s %s" % (u, src, what))

    for u in units:
        for x in names:
            if rng.random() < pshut:
                lines.append("%s shut %s" % (u, x))
            if rng.random() < phide:
                lines.append("%s hide %s" % (u, x))

    rng.shuffle(lines)

    asks = []
    for _ in range(nask):
        u = rng.choice(units)
        x = rng.choice(list(names) + list(TAGS))
        asks.append("%s ask %s" % (u, x))
    return lines + asks


def _late(rng):
    """Two origins meeting at one unit at equal rank, with the chains declared apart.

    The rules never mention declaration order, so this shape settles the same way whichever
    order the lines arrive in. An engine that settles a name as soon as one route reaches it,
    and carries that answer onward before the second route arrives, does not.
    """
    hops = rng.randint(1, 3)
    names = _names(2)
    lines = []
    left = ["l%d" % i for i in range(hops)]
    right = ["r%d" % i for i in range(hops)]
    x = names[0]
    lines.append("o0 own %s" % x)
    lines.append("o1 own %s" % x)
    for side, chain in (("o0", left), ("o1", right)):
        prev = side
        for nm in chain:
            lines.append("%s pull %s %s" % (nm, prev, "*" if rng.random() < 0.6 else x))
            prev = nm
    meet = "m0"
    lines.append("%s pull %s *" % (meet, left[-1]))
    lines.append("%s pull %s *" % (meet, right[-1]))
    if rng.random() < 0.5:
        lines.append("%s own %s" % (rng.choice(left + right), names[1]))
    tail = ["t%d" % i for i in range(rng.randint(1, 2))]
    prev = meet
    for nm in tail:
        lines.append("%s pull %s *" % (nm, prev))
        prev = nm
    if rng.random() < 0.4:
        lines.append("%s pull %s %s" % (tail[0], rng.choice(left), x))

    early = set(left) | {"o0"}
    head = [ln for ln in lines if ln.split()[0] in early]
    rest = [ln for ln in lines if ln.split()[0] not in early]
    rng.shuffle(rest)
    lines = head + rest

    asks = ["%s ask %s" % (u, x) for u in [meet] + tail + [left[-1], right[-1]]]
    asks += ["%s ask %s" % (rng.choice(tail + [meet]), names[1])]
    return lines + asks


def programs(seed, per):
    out = []
    for fam, share in FAMILIES:
        want = max(1, (per * share) // 100)
        for i in range(want):
            rng = random.Random("%s:%s:%d" % (seed, fam, i))
            out.append((fam, "%s-%03d" % (fam, i), build(fam, rng)))
    return out
