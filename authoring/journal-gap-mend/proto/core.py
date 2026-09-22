"""Prototype semantics for the lock-service journal (scratch, not shipped).

A table is a tuple over locks of (holder, depth, queue); holder None when free.
Totals: g grants (an acquisition that takes a free lock, or a hand-off at release),
a acquisition requests, r releases, b heartbeats.

Rules can be bent by flags so that wrong readings can be measured against the right one.
"""
import hashlib


class Rules:
    def __init__(self, depth=True, pass_counts=True, silence=True, beat_hold=True,
                 queue=True):
        self.depth = depth            # reentrant acquisitions raise depth; release lowers it
        self.pass_counts = pass_counts  # a hand-off at release counts as a grant
        self.silence = silence        # a waiting session sends nothing
        self.beat_hold = beat_hold    # a heartbeat needs a held lock
        self.queue = queue            # a refused acquisition joins a first-come queue


RIGHT = Rules()


def fp(state):
    s = ",".join("-" if h is None else str(h) for (h, _d, _q) in state)
    return hashlib.sha256(s.encode()).hexdigest()[:10]


def ffp(state):
    s = ";".join("%s/%d/%s" % ("-" if h is None else h, d, ".".join(map(str, q)))
                 for (h, d, q) in state)
    return hashlib.sha256(s.encode()).hexdigest()[:10]


def initial(nlocks):
    return tuple((None, 0, ()) for _ in range(nlocks))


def waiting(state, s):
    return any(s in q for (_h, _d, q) in state)


def holds_any(state, s):
    return any(h == s for (h, _d, _q) in state)


def label(e):
    if e[0] == "beat":
        return "beat %d" % e[1]
    return "%s %d %d %s" % e


def apply(state, req, rules=RIGHT):
    """Apply a request. Returns (entry, state', dg, da, dr, db) or None when illegal."""
    kind = req[0]
    if kind == "beat":
        s = req[1]
        if rules.silence and waiting(state, s):
            return None
        if rules.beat_hold and not holds_any(state, s):
            return None
        return (("beat", s), state, 0, 0, 0, 1)
    l, s = req[1], req[2]
    if rules.silence and waiting(state, s):
        return None
    h, d, q = state[l]
    st = list(state)
    if kind == "acq":
        if h is None:
            st[l] = (s, 1, q)
            return (("acq", l, s, "grant"), tuple(st), 1, 1, 0, 0)
        if h == s:
            if rules.depth:
                st[l] = (h, d + 1, q)
            return (("acq", l, s, "again"), tuple(st), 0, 1, 0, 0)
        if rules.queue:
            if s in q:
                return None if rules.silence else (("acq", l, s, "wait"), state, 0, 1, 0, 0)
            st[l] = (h, d, q + (s,))
        return (("acq", l, s, "wait"), tuple(st), 0, 1, 0, 0)
    # release
    if h != s:
        return None
    nd = d - 1 if rules.depth else 0
    if nd > 0:
        st[l] = (h, nd, q)
        return (("rel", l, s, "keep"), tuple(st), 0, 0, 1, 0)
    if not q:
        st[l] = (None, 0, q)
        return (("rel", l, s, "free"), tuple(st), 0, 0, 1, 0)
    st[l] = (q[0], 1, q[1:])
    return (("rel", l, s, "pass"), tuple(st), 1 if rules.pass_counts else 0, 0, 1, 0)


def requests(state, nlocks, nsess):
    """Every request a table could be offered, legal or not (apply decides)."""
    out = []
    for l in range(nlocks):
        for s in range(nsess):
            out.append(("acq", l, s))
    for l in range(nlocks):
        h = state[l][0]
        if h is not None:
            out.append(("rel", l, h))
    for s in range(nsess):
        out.append(("beat", s))
    return out


# ---- journal text -------------------------------------------------------------------

def parse(text):
    lines = [ln.split() for ln in text.strip().splitlines() if ln.strip()]
    head = lines[0]
    assert head[0] == "cfg"
    cfg = tuple(int(x) for x in head[1:4])
    items = []
    i = 1
    while i < len(lines):
        w = lines[i]
        if w[0] == "gap":
            marks = []
            i += 1
            while lines[i][0] != "back":
                v = lines[i]
                if v[0] == "dig":
                    marks.append(("d", int(v[1]), v[2]))
                else:
                    marks.append(("s", int(v[1]), int(v[2]), int(v[3]), int(v[4]), v[5]))
                i += 1
            items.append(("gap", marks))
        elif w[0] == "dig":
            items.append(("d", int(w[1]), w[2]))
        elif w[0] == "sum":
            items.append(("s", int(w[1]), int(w[2]), int(w[3]), int(w[4]), w[5]))
        elif w[0] == "beat":
            items.append(("e", ("beat", int(w[1]))))
        else:
            items.append(("e", (w[0], int(w[1]), int(w[2]), w[3])))
        i += 1
    return cfg, items


def fmt(cfg, items):
    out = ["cfg %d %d %d" % cfg]
    for it in items:
        if it[0] == "e":
            out.append(label(it[1]))
        elif it[0] == "d":
            out.append("dig %d %s" % (it[1], it[2]))
        elif it[0] == "s":
            out.append("sum %d %d %d %d %s" % it[1:])
        else:
            out.append("gap")
            for m in it[1]:
                if m[0] == "d":
                    out.append("dig %d %s" % m[1:])
                else:
                    out.append("sum %d %d %d %d %s" % m[1:])
            out.append("back")
    return "\n".join(out) + "\n"
