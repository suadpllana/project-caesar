"""Nonce program generation.

Eight families. `plain` is an unshaped mix and is what an agent's own testing will mostly look
like. The rest seed shapes a plain population almost never builds: `chain` a pair cascade,
`hold` a finalizer closure that reaches a pair key, `back` a resurrection, `rset` an old-space
field pointing into the nursery and then going stale, and `wide` a pair table written back to
front, which is the family a collector that rescans the table cannot finish.

`reuse` hands a released number back out. Nothing in an unshaped population does this often
enough to matter, and every record the runtime keeps about an object - whether its finalizer has
run, which object a pair row was written about - has to answer for the object rather than for
the number. Half its programs retire a finalized object and re-allocate its number; half kill the
key of a pair row and re-allocate that.

`sweep` is the family that decides what a minor collection is allowed to cost. It builds a large
old space held by a single root, then runs many minor collections against a nursery of one or two
objects. Every answer in it is ordinary; what it measures is whether the collection's work is
proportional to the nursery or to the whole heap and to every store the program has ever made.

Programs stay well formed: an op never names a number whose object an earlier collection
released without allocating there again first, so the generator replays the model over what it
has emitted and draws only from what survives. Every collection is sorted before use, so a
program depends on its seed and nothing else.
"""
import random

import model

SLOTS = ("a", "b", "c")
GLOBS = ("g1", "g2")
FIELDS = ("x", "y", "z")

WIDE_COUNT = 12
SWEEP_COUNT = 6


def _ops(lines):
    return [tuple(ln.split()) for ln in lines]


def _alive(lines):
    return model.alive(_ops(lines))


def _released(lines, known):
    """Numbers that were live in `known` and whose objects a collection has since released."""
    live = set(_alive(lines))
    return sorted(i for i in known if i not in live)


def _new(rng, out, i, fin_rate):
    if rng.random() < fin_rate:
        if rng.random() < 0.5:
            out.append("new %d fin %s" % (i, rng.choice(SLOTS)))
        else:
            out.append("new %d fin" % i)
    else:
        out.append("new %d" % i)


def _plain(rng):
    out, nxt, wk, depth, held = [], 1, 0, 1, 0
    for _ in range(rng.randint(5, 10)):
        _new(rng, out, nxt, 0.25)
        nxt += 1
    for _ in range(rng.randint(10, 22)):
        ids = _alive(out)
        if not ids:
            _new(rng, out, nxt, 0.3)
            nxt += 1
            continue
        r = rng.random()
        if r < 0.18:
            out.append("set %d %s %d" % (rng.choice(ids), rng.choice(FIELDS), rng.choice(ids)))
        elif r < 0.32:
            t = rng.choice(ids + [None])
            out.append("slot %s %s" % (rng.choice(SLOTS), "-" if t is None else str(t)))
        elif r < 0.42:
            t = rng.choice(ids + [None])
            out.append("glob %s %s" % (rng.choice(GLOBS), "-" if t is None else str(t)))
        elif r < 0.54:
            out.append("pair %d %d" % (rng.choice(ids), rng.choice(ids)))
        elif r < 0.62:
            wk += 1
            out.append("weak w%d %d" % (wk, rng.choice(ids)))
        elif r < 0.68:
            out.append("hold %d" % rng.choice(ids))
            held += 1
        elif r < 0.72:
            if held:
                out.append("drop")
                held -= 1
        elif r < 0.76:
            out.append("pin %d" % rng.choice(ids))
        elif r < 0.79:
            out.append("unpin %d" % rng.choice(ids))
        elif r < 0.83:
            out.append("push")
            depth += 1
        elif r < 0.86:
            if depth > 1:
                out.append("pop")
                depth -= 1
        elif r < 0.90:
            _new(rng, out, nxt, 0.3)
            nxt += 1
        elif r < 0.97:
            out.append("collect")
        else:
            out.append("collectfull")
    out.append("collect")
    out.append("collectfull")
    return out


def _chain(rng):
    n = rng.randint(5, 9)
    out = []
    for i in range(1, n + 1):
        _new(rng, out, i, 0.15)
    link = list(range(1, n + 1))
    rng.shuffle(link)
    steps = [(link[i], link[i + 1]) for i in range(min(len(link) - 1, rng.randint(2, 4)))]
    for k, v in reversed(steps):
        out.append("pair %d %d" % (k, v))
    out.append("slot a %d" % steps[0][0])
    out.append("collect")
    if rng.random() < 0.5:
        out += ["collect", "collectfull"]
    return out


def _hold(rng):
    n = rng.randint(5, 9)
    out = ["new 1 fin" if rng.random() < 0.5 else "new 1 fin %s" % rng.choice(SLOTS)]
    for i in range(2, n + 1):
        _new(rng, out, i, 0.0)
    if rng.random() < 0.45:
        out[1] = "new 2 fin"
    out.append("set 1 %s 2" % rng.choice(FIELDS))
    out.append("pair 2 3")
    if rng.random() < 0.5:
        out.append("weak w1 1")
    if rng.random() < 0.4:
        out.append("pin 1")
    out += ["collect", "collect"]
    if rng.random() < 0.6:
        out += ["runfin", "collect"]
    return out


def _back(rng):
    n = rng.randint(4, 7)
    s = rng.choice(SLOTS)
    out = ["new 1 fin %s" % s]
    for i in range(2, n + 1):
        _new(rng, out, i, 0.2)
    if rng.random() < 0.7:
        out.append("weak w1 1")
    out += ["collect", "runfin", "collect", "slot %s -" % s, "collect", "collectfull"]
    return out


def _rset(rng):
    # Half promote with the edge already installed; half exercise a later old-to-nursery write.
    # Both routes must enter the remembered set, and both can leave a stale record afterwards.
    promote_with_edge = rng.random() < 0.5
    out = ["new 1", "slot a 1", "collect"]
    if not promote_with_edge:
        out.append("collect")
    nxt = 2
    for _ in range(rng.randint(2, 4)):
        out.append("new %d" % nxt)
        nxt += 1
    out.append("set 1 x 2")
    if nxt > 3 and rng.random() < 0.5:
        # a second field of the same old object, so the entries cannot be collapsed by source
        out.append("set 1 y 3")
    if nxt > 3 and rng.random() < 0.5:
        out.append("pair 2 3")
    out.append("collect")
    r = rng.random()
    if r < 0.4:
        out.append("set 1 x -")
    elif r < 0.7:
        out.append("set 1 x %d" % (nxt - 1))
    out.append("collect")
    if rng.random() < 0.5:
        out += ["slot a -", "collectfull"]
    return out


def _wide(rng):
    depth = rng.choice((10000, 13000, 16000))
    bulk = rng.choice((3000, 5000))
    out = ["new %d" % i for i in range(1, depth + 2)]
    out += ["pair %d %d" % (i, i + 1) for i in range(depth, 0, -1)]
    base = depth + 2
    for k in range(bulk):
        a, b = base + 2 * k, base + 2 * k + 1
        out += ["new %d" % a, "new %d" % b, "pair %d %d" % (a, b)]
    out += ["slot a 1", "collect"]
    if rng.random() < 0.5:
        out += ["slot a -", "collectfull"]
    return out


def _reuse(rng):
    # Both halves retire an object and hand its number straight back out, so the record the
    # runtime kept about the object that has gone is asked to answer for the one that arrives.
    # Half leave behind a finalizer that has already run; half leave behind a pair row.
    by_finalizer = rng.random() < 0.5
    last = rng.randint(2, 4)
    out = ["new 1 fin" if by_finalizer else "new 1"]
    for i in range(2, last + 1):
        out.append("new %d" % i)

    if by_finalizer:
        out.append("slot b %d" % last)
        out += ["collect", "runfin", "collect"]
    else:
        out += ["pair 1 %d" % last, "slot a %d" % last, "collect"]

    if 1 not in _released(out, set(range(1, last + 1))):
        raise AssertionError("reuse family failed to free number 1")

    out.append("new 1 fin")
    if rng.random() < 0.5:
        out.append("weak w1 1")
    out += ["slot c 1", "collect", "slot c -"]
    if not by_finalizer:
        out.append("slot a -")
    out.append("collect")
    if rng.random() < 0.5:
        out.append("collectfull")
    return out


def _sweep(rng):
    survivors = rng.choice((14000, 16000, 18000))
    rounds = rng.choice((6000, 7000))
    anchors = list(range(1, rng.randint(3, 5) + 1))

    out = ["new 1", "glob g1 1"]
    prev, nxt = 1, 2
    for _ in range(survivors - 1):
        out.append("new %d" % nxt)
        out.append("set %d n %d" % (prev, nxt))
        prev, nxt = nxt, nxt + 1
    out += ["collect", "collect"]

    for _ in range(rounds):
        out.append("new %d" % nxt)
        out.append("slot a %d" % nxt)
        for a in anchors:
            out.append("set %d e %d" % (a, nxt))
        nxt += 1
        out.append("collect")
    if rng.random() < 0.5:
        out.append("collectfull")
    return out


FAMILIES = (("plain", _plain), ("chain", _chain), ("hold", _hold),
            ("back", _back), ("rset", _rset), ("reuse", _reuse),
            ("wide", _wide), ("sweep", _sweep))


FIXED = {"wide": WIDE_COUNT, "sweep": SWEEP_COUNT}


def programs(seed, per_family):
    out = []
    for fam, fn in FAMILIES:
        n = FIXED.get(fam, per_family)
        for k in range(n):
            rng = random.Random("%s:%s:%d" % (seed, fam, k))
            out.append((fam, "%s-%03d" % (fam, k), fn(rng)))
    return out


def ops(lines):
    return _ops(lines)
