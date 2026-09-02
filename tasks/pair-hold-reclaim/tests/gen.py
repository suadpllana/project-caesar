"""The generated stream set.

Built inside the verifier from a nonce made after the agent has finished, so the streams
graded here did not exist while the submission was being written. Every collection is
turned into a sequence through a sorted list before it is sampled: the runner builds
these streams in one process and the grader rebuilds them in another, and a generator
that iterates a set of strings builds a different stream in each.

The mix is deliberate rather than uniform. Two-key entries are placed so that one key is
held from a name and the other sits inside a group that is going out of reach, chains of
one-key entries are laid through links so that a single sweep of the tables cannot
settle them, and cleanup actions unbind names and cut links about as often as they bind
and add, so a pass that stops after one round leaves work behind.
"""

import random

ACTS = ("bind", "unbind", "edge", "cut", "pair", "both", "look", "none")


def _stream(rng):
    n = rng.randint(8, 15)
    ids = list(range(1, n + 1))
    lines = ["new %d" % i for i in ids]
    names = ["h%d" % k for k in range(rng.randint(1, 3))]
    fixed = ["mk", "mc"]
    armed = []
    watched = []
    out = []
    kept = ids[-3:]
    spoken = _motifs(rng, ids[:-3], kept, fixed, armed)
    lines.extend(spoken)
    open_ids = ids[:-3]

    for a in open_ids:
        for b in open_ids:
            if a != b and rng.random() < 0.15:
                lines.append("edge %d %d" % (a, b))
    for _ in range(rng.randint(0, 3)):
        k = rng.choice(open_ids)
        v = rng.choice([i for i in open_ids if i != k])
        lines.append("pair %d %d" % (k, v))
    for _ in range(rng.randint(0, 3)):
        a = rng.choice(open_ids)
        b = rng.choice([i for i in open_ids if i != a])
        v = rng.choice([i for i in open_ids if i not in (a, b)])
        lines.append("both %d %d %d" % (a, b, v))
    for nm in names:
        lines.append("bind %s %d" % (nm, rng.choice(open_ids)))
    for _ in range(rng.randint(1, 4)):
        w = "w%d" % len(watched)
        watched.append(w)
        lines.append("watch %s %s %d" % (w, rng.choice(["plain", "firm"]), rng.choice(ids)))
    for i in open_ids:
        if i not in armed and rng.random() < 0.40:
            armed.append(i)
            lines.append("arm %d %s" % (i, _act(rng, open_ids, names, watched)))

    out.extend(lines)
    for _ in range(rng.randint(2, 4)):
        for _ in range(rng.randint(0, 3)):
            out.append(_mut(rng, open_ids, names))
        out.append("pass")
        for w in watched:
            if rng.random() < 0.5:
                out.append("show %s" % w)
    return "\n".join(out) + "\n"


def _motifs(rng, ids, kept, names, armed):
    """Shapes the uniform sampler almost never reaches, planted on purpose.

    A straddling two-key entry, one key held from a name and the other inside the group
    going out of reach, is what separates the two seeds the ordering question can be
    asked with. A chain of one-key entries laid through a link is what a single sweep of
    the tables cannot settle. A pair of cells that can each reach the other, one of them
    putting the other back, is what separates letting a blocked group go together from
    letting the oldest go alone.
    """
    out = []
    pool = list(ids)
    if len(pool) < 6:
        return out
    rng.shuffle(pool)
    h = kept[rng.randrange(3)]
    v, p = sorted([c for c in kept if c != h])
    out.append("bind %s %d" % (names[0], h))
    out.append("both %d %d %d" % (p, h, v))
    for c in (v, p):
        armed.append(c)
        out.append("arm %d none" % c)
    if rng.random() < 0.6:
        k1, v1, k2, v2 = pool[0], pool[1], pool[2], pool[rng.randrange(len(pool))]
        if len({k1, v1, k2, v2}) == 4:
            out.append("bind %s %d" % (names[1], k1))
            out.append("pair %d %d" % (k1, v1))
            out.append("edge %d %d" % (v1, k2))
            out.append("pair %d %d" % (k2, v2))
    if rng.random() < 0.5 and len(pool) >= 6:
        a, b = pool[3], pool[4]
        out.append("edge %d %d" % (a, b))
        out.append("edge %d %d" % (b, a))
        if a not in armed:
            armed.append(a)
            out.append("arm %d bind %s %d" % (a, names[1], b))
        if b not in armed:
            armed.append(b)
            out.append("arm %d none" % b)
    return out

def _act(rng, ids, names, watched):
    head = rng.choice(ACTS)
    if head == "bind":
        return "bind %s %d" % (rng.choice(names), rng.choice(ids))
    if head == "unbind":
        return "unbind %s" % rng.choice(names)
    if head in ("edge", "cut"):
        a = rng.choice(ids)
        b = rng.choice([i for i in ids if i != a])
        return "%s %d %d" % (head, a, b)
    if head == "pair":
        k = rng.choice(ids)
        v = rng.choice([i for i in ids if i != k])
        return "pair %d %d" % (k, v)
    if head == "both":
        a = rng.choice(ids)
        b = rng.choice([i for i in ids if i != a])
        v = rng.choice([i for i in ids if i not in (a, b)])
        return "both %d %d %d" % (a, b, v)
    if head == "look" and watched:
        return "look %s" % rng.choice(watched)
    return "none"


def _mut(rng, ids, names):
    pick = rng.randint(0, 4)
    if pick == 0:
        return "bind %s %d" % (rng.choice(names), rng.choice(ids))
    if pick == 1:
        return "unbind %s" % rng.choice(names)
    if pick == 2:
        a = rng.choice(ids)
        b = rng.choice([i for i in ids if i != a])
        return "cut %d %d" % (a, b)
    if pick == 3:
        a = rng.choice(ids)
        b = rng.choice([i for i in ids if i != a])
        return "edge %d %d" % (a, b)
    k = rng.choice(ids)
    v = rng.choice([i for i in ids if i != k])
    return "pair %d %d" % (k, v)


def build(nonce, count):
    out = []
    for k in range(count):
        rng = random.Random("%s:%d" % (nonce, k))
        out.append(("g%04d" % k, _stream(rng)))
    return out
