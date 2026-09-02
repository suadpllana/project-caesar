"""Build plans from a nonce.

The nonce is made from /dev/urandom inside the verifier container after the agent
has finished, so nothing here can be answered in advance. The run may read this
file: knowing how plans are shaped produces none of their traces.

Everything that becomes a sequence is sorted first. The runner builds these plans
in one process and the grader rebuilds them in another, and Python randomises
string hashing per process, so a set or a dict iterated without sorting would give
the two processes different plans under the same nonce and fail a correct
submission on whichever ones differed.

`ok` rejects a plan the machine cannot run to a finish in a sensible number of
ticks. Every node passes what it takes to all of its out edges, so a plan with a
lot of branching and a cheap way back multiplies items faster than the horizon
retires them; the budget below is structural on purpose, since this file must not
be able to run the machine.
"""

import hashlib
import random


def seed(nonce, i):
    h = hashlib.sha256(("%s|%d" % (nonce, i)).encode("utf-8")).digest()
    return int.from_bytes(h[:8], "big")


def shape(rng):
    src = ["s%d" % i for i in range(rng.randint(1, 2))]
    mid = ["r%d" % i for i in range(rng.randint(1, 3))]
    mid += ["f%d" % i for i in range(rng.randint(1, 2))]
    gat = ["g%d" % i for i in range(rng.randint(1, 2))]
    body = sorted(mid) + gat
    rng.shuffle(body)
    return src, body, gat, ["k0"]


def build(rng):
    src, body, gat, snk = shape(rng)
    rank = src + body + snk
    kind, par = {}, {}
    for n in rank:
        if n in src:
            kind[n], par[n] = "src", 0
        elif n in snk:
            kind[n], par[n] = "sink", 0
        elif n in gat:
            kind[n] = "gather"
            par[n] = rng.choice([4, 5, 6, 8, 10, 12])
        elif n.startswith("f"):
            kind[n] = "lift"
            par[n] = rng.choice([8, 12, 20, 25, 33, 40])
        else:
            kind[n], par[n] = "relay", 0
    edge = set()
    for i, a in enumerate(rank):
        if kind[a] == "sink":
            continue
        picks = [x for x in rank[i + 1:] if kind[x] != "src"]
        if kind[a] == "src":
            near = [x for x in picks if kind[x] not in ("gather", "sink")]
            picks = near or picks
        if not picks:
            continue
        want = 2 if rng.random() < 0.45 else 1
        for b in rng.sample(picks, min(want, len(picks))):
            edge.add((a, b, rng.choice([0, 0, 1, 2, 3, 5])))
    for i, b in enumerate(rank):
        if kind[b] == "src":
            continue
        if not any(e[1] == b for e in sorted(edge)):
            cand = [x for x in rank[:i] if kind[x] != "sink"]
            edge.add((rng.choice(cand), b, rng.choice([0, 1, 2])))
    for i, a in enumerate(rank):
        if kind[a] == "sink":
            continue
        if not any(e[0] == a for e in sorted(edge)):
            cand = [x for x in rank[i + 1:] if kind[x] != "src"]
            edge.add((a, rng.choice(cand), rng.choice([0, 1, 2])))
    gats = [n for n in rank if kind[n] == "gather"]
    if len(gats) > 1 and rng.random() < 0.7:
        a, b = gats[0], gats[1]
        edge.add((a, b, rng.choice([0, 1, 2])))
    for _ in range(2):
        if rng.random() > 0.55:
            continue
        a = rng.choice([x for x in rank if kind[x] in ("relay", "lift", "gather")])
        cand = [x for x in rank[:rank.index(a)] if kind[x] not in ("src", "sink")]
        if cand:
            edge.add((a, rng.choice(cand), rng.choice([3, 4, 5, 6, 8, 10])))
    hz = rng.choice([36, 44, 55, 60, 70, 84])
    return rank, kind, par, sorted(edge), src, hz


def script(rng, src, hz):
    ev = []
    for n in sorted(src):
        t = rng.randint(1, 2)
        low = 0
        ev.append((t, "put", n, rng.randint(0, max(0, min(hz - 1, 12)))))
        t += rng.randint(1, 3)
        for _ in range(rng.randint(3, 6)):
            if rng.random() < 0.5:
                ev.append((t, "put", n, rng.randint(low, max(low, min(hz - 1, low + 20)))))
            else:
                low = min(hz - 1, low + rng.randint(2, 12))
                ev.append((t, "low", n, low))
            t += rng.randint(1, 5)
        ev.append((t + rng.randint(0, 4), "shut", n, 0))
    ev.sort(key=lambda r: (r[0], r[2], r[1], r[3]))
    return ev


def one(nonce, i):
    rng = random.Random(seed(nonce, i))
    rank, kind, par, edge, src, hz = build(rng)
    return {"hz": hz, "order": sorted(rank), "kind": kind, "par": par,
            "edge": edge, "ev": script(rng, src, hz)}


def text(p):
    out = ["hz %d" % p["hz"]]
    for n in p["order"]:
        k = p["kind"][n]
        tail = (" %d" % p["par"][n]) if k in ("lift", "gather") else ""
        out.append("node %s %s%s" % (n, k, tail))
    for a, b, lag in p["edge"]:
        out.append("wire %s %s %d" % (a, b, lag))
    for t, op, n, v in p["ev"]:
        out.append("%s %d %s%s" % (op, t, n, "" if op == "shut" else " %d" % v))
    return "\n".join(out) + "\n"


def loops(p):
    """The lightest way back to where you started, over every cycle in the plan.

    A depth-first walk that blackens what it has seen misses cycles it reaches by
    a second route, and a plan whose real cycle is lighter than the one that walk
    found runs far longer than the budget below expects. This is the closure
    instead: shortest paths of at least one edge, then the lightest round trip.
    """
    far = {}
    for a, b, w in p["edge"]:
        if (a, b) not in far or w < far[(a, b)]:
            far[(a, b)] = w
    for m in p["order"]:
        for a in p["order"]:
            if (a, m) not in far:
                continue
            for b in p["order"]:
                if (m, b) not in far:
                    continue
                w = far[(a, m)] + far[(m, b)]
                if (a, b) not in far or w < far[(a, b)]:
                    far[(a, b)] = w
    return sorted(far[(n, n)] for n in p["order"] if (n, n) in far)


def flat(p):
    grey, black = set(), set()

    def walk(n):
        grey.add(n)
        for a, b, w in p["edge"]:
            if a != n or w:
                continue
            if b in grey:
                return True
            if b not in black and walk(b):
                return True
        grey.discard(n)
        black.add(n)
        return False

    for n in p["order"]:
        if n not in black and walk(n):
            return True
    return False


def ok(p):
    if flat(p):
        return False
    live = set(n for n in p["order"] if p["kind"][n] == "src")
    grow = True
    while grow:
        grow = False
        for a, b, lag in p["edge"]:
            if a in live and b not in live:
                live.add(b)
                grow = True
    if any(n not in live for n in p["order"]):
        return False
    gat = [n for n in p["order"] if p["kind"][n] == "gather"]
    if not gat:
        return False
    if not any(all(p["kind"][a] != "src" for a, b, w in p["edge"] if b == g) for g in gat):
        return False
    fan = sum(max(0, len([e for e in p["edge"] if e[0] == n]) - 1)
              for n in p["order"] if p["kind"][n] != "sink")
    ring = loops(p)
    if ring:
        turns = p["hz"] // max(1, min(ring))
        if fan * turns > 22 or turns > 14:
            return False
    elif fan > 5:
        return False
    return True


def batch(nonce, n):
    out, i = [], 0
    while len(out) < n:
        p = one(nonce, i)
        i += 1
        if ok(p):
            out.append(("z%04d" % len(out), p))
        if i > n * 60:
            raise RuntimeError("gen")
    return out
