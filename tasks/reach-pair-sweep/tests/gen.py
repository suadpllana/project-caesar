"""Nonce program generation.

Five families. `plain` is an unshaped mix and is what an agent's own testing will mostly look
like; measurement on 600 unshaped programs put the retention cascade in under 4% of them, so
`chain`, `hold` and `back` seed the shapes a plain population almost never builds.

Programs stay well formed: an op never names an object an earlier collection released, so the
generator replays the model over what it has emitted so far and draws only from what survives.
Every collection is sorted before use, so a program depends on its seed and nothing else.
"""
import random

import model

SLOTS = ("a", "b", "c")
FIELDS = ("x", "y", "z")


def _ops(lines):
    return [tuple(ln.split()) for ln in lines]


def _alive(lines):
    return model.alive(_ops(lines))


def _new(rng, out, i, fin_rate):
    if rng.random() < fin_rate:
        if rng.random() < 0.5:
            out.append("new %d fin %s" % (i, rng.choice(SLOTS)))
        else:
            out.append("new %d fin" % i)
    else:
        out.append("new %d" % i)


def _plain(rng):
    out, nxt, wk, depth = [], 1, 0, 1
    for _ in range(rng.randint(6, 12)):
        _new(rng, out, nxt, 0.28)
        nxt += 1
    for _ in range(rng.randint(6, 18)):
        ids = _alive(out)
        r = rng.random()
        if not ids:
            _new(rng, out, nxt, 0.3)
            nxt += 1
            continue
        if r < 0.24:
            out.append("set %d %s %d" % (rng.choice(ids), rng.choice(FIELDS), rng.choice(ids)))
        elif r < 0.44:
            t = rng.choice(ids + [None])
            out.append("slot %s %s" % (rng.choice(SLOTS), "-" if t is None else str(t)))
        elif r < 0.62:
            out.append("pair %d %d" % (rng.choice(ids), rng.choice(ids)))
        elif r < 0.72:
            wk += 1
            out.append("weak w%d %d" % (wk, rng.choice(ids)))
        elif r < 0.78:
            out.append("push")
            depth += 1
        elif r < 0.82:
            if depth > 1:
                out.append("pop")
                depth -= 1
        elif r < 0.88:
            _new(rng, out, nxt, 0.3)
            nxt += 1
        elif r < 0.96:
            out.append("collect")
        else:
            out.append("runfin")
    out.append("collect")
    return out


def _chain(rng):
    """Pairs where each value is the next pair's key, listed back to front."""
    n = rng.randint(5, 9)
    out = []
    for i in range(1, n + 1):
        _new(rng, out, i, 0.15)
    link = list(range(1, n + 1))
    rng.shuffle(link)
    depth = min(len(link) - 1, rng.randint(2, 4))
    steps = [(link[i], link[i + 1]) for i in range(depth)]
    for k, v in reversed(steps):
        out.append("pair %d %d" % (k, v))
    out.append("slot a %d" % steps[0][0])
    for _ in range(rng.randint(0, 2)):
        ids = _alive(out)
        out.append("set %d %s %d" % (rng.choice(ids), rng.choice(FIELDS), rng.choice(ids)))
    out.append("collect")
    if rng.random() < 0.4:
        out += ["slot a -", "collect"]
    return out


def _hold(rng):
    """A finalizable object whose own closure reaches the key of a pair."""
    n = rng.randint(5, 9)
    out = ["new 1 fin" if rng.random() < 0.5 else "new 1 fin %s" % rng.choice(SLOTS)]
    for i in range(2, n + 1):
        _new(rng, out, i, 0.0)
    out.append("set 1 %s 2" % rng.choice(FIELDS))
    out.append("pair 2 3")
    if n > 3 and rng.random() < 0.6:
        out.append("pair 3 4")
    if rng.random() < 0.5:
        out.append("weak w1 1")
    if rng.random() < 0.4:
        out.append("slot b %d" % n)
    out.append("collect")
    if rng.random() < 0.6:
        out += ["runfin", "collect"]
    return out


def _back(rng):
    """Stored back by its own finalizer, then dropped again."""
    n = rng.randint(4, 7)
    s = rng.choice(SLOTS)
    out = ["new 1 fin %s" % s]
    for i in range(2, n + 1):
        _new(rng, out, i, 0.2)
    if rng.random() < 0.7:
        out.append("weak w1 1")
    if rng.random() < 0.5:
        out.append("pair 1 2")
    out += ["collect", "runfin", "collect", "slot %s -" % s, "collect"]
    if rng.random() < 0.4:
        out += ["runfin", "collect"]
    return out



def _wide(rng):
    """A chain of pairs listed back to front, plus bulk the chain never reaches.

    Back to front is the whole point: listed forwards the chain settles in one sweep. Listed
    backwards, a collector that rescans the table settles exactly one link per sweep, so its
    cost is the table size times the depth. The bulk pairs live on ids nothing reaches, so they
    add to every sweep without ever letting two links fire at once.
    """
    depth = rng.choice((10000, 13000, 16000))
    bulk = rng.choice((3000, 5000))
    out = ["new %d" % i for i in range(1, depth + 2)]
    out += ["pair %d %d" % (i, i + 1) for i in range(depth, 0, -1)]
    base = depth + 2
    for k in range(bulk):
        a, b = base + 2 * k, base + 2 * k + 1
        out.append("new %d" % a)
        out.append("new %d" % b)
        out.append("pair %d %d" % (a, b))
    out.append("slot a 1")
    out.append("collect")
    if rng.random() < 0.5:
        out += ["slot a -", "collect"]
    return out


FAMILIES = (("plain", _plain), ("chain", _chain), ("hold", _hold), ("back", _back), ("wide", _wide))


# `wide` programs are tens of thousands of lines each, so the population is sized separately:
# enough of them that a collector settling the pair table by rescanning cannot finish, few
# enough that a correct one costs a fraction of a second.
WIDE_COUNT = 15


def programs(seed, per_family):
    """Deterministic list of (family, name, lines) for one nonce seed."""
    out = []
    for fam, fn in FAMILIES:
        n = WIDE_COUNT if fam == "wide" else per_family
        for k in range(n):
            rng = random.Random("%s:%s:%d" % (seed, fam, k))
            out.append((fam, "%s-%03d" % (fam, k), fn(rng)))
    return out


def ops(lines):
    return _ops(lines)
