"""Independent model of the matching rules, written from the specification.

Shares no code with the tree, and decides each of the graded questions by a different
route.

  The book. The tree keeps each side as a dict of price levels holding deques, with lazy
  price heaps and dead orders skipped on the way past. This keeps one flat list per side
  and finds the best price and the queue front by scanning it, with queue position held
  in an explicit sequence number that is bumped when an order re-discloses rather than by
  moving the record.

  All or nothing. The tree decides admission with a read-only probe across the levels and
  then walks for real. This walks for real straight away, recording every change it makes
  into a trail, and rewinds the trail when the order comes up short.

  Activation. The tree keeps the parked orders in two heaps. This buckets them by trip
  price and finds the tripped range by bisecting a sorted list of distinct trip prices.

  Parsing is separate too.

The two therefore agree only if they agree about the rules.
"""

import bisect


class Rec:
    def __init__(self, oid, hand, side, px, qty, shw, tif, trp):
        self.oid = oid
        self.hand = hand
        self.side = side
        self.px = px
        self.rem = qty
        self.shw = shw
        self.shn = qty if shw is None else min(shw, qty)
        self.tif = tif
        self.trp = trp
        self.seq = 0


class Pen:
    """Parked orders, bucketed by trip price."""

    def __init__(self):
        self.pri = {"b": [], "s": []}
        self.bag = {"b": {}, "s": {}}

    def add(self, o):
        bag = self.bag[o.side]
        if o.trp not in bag:
            bag[o.trp] = []
            bisect.insort(self.pri[o.side], o.trp)
        bag[o.trp].append(o)

    def gone(self, o):
        bag = self.bag[o.side][o.trp]
        bag.remove(o)
        if not bag:
            del self.bag[o.side][o.trp]
            self.pri[o.side].remove(o.trp)

    def has(self, oid):
        for side in ("b", "s"):
            for bag in self.bag[side].values():
                for o in bag:
                    if o.oid == oid:
                        return o
        return None

    def fired(self, last):
        out = []
        keys = self.pri["b"]
        for k in keys[:bisect.bisect_right(keys, last)]:
            out.extend(self.bag["b"][k])
        keys = self.pri["s"]
        for k in keys[bisect.bisect_left(keys, last):]:
            out.extend(self.bag["s"][k])
        return out

    def rest(self):
        out = []
        for side in ("b", "s"):
            for bag in self.bag[side].values():
                out.extend(bag)
        return sorted(out, key=lambda o: o.oid)


class State:
    def __init__(self, cap, mark):
        self.cap = cap
        self.last = mark
        self.bk = {"b": [], "s": []}
        self.pen = Pen()
        self.pend = []
        self.seq = 0
        self.rows = []

    def row(self, *cells):
        self.rows.append(tuple(cells))


def parse(text):
    cap = 0
    mark = 0
    msgs = []
    for raw in text.splitlines():
        f = raw.split()
        if not f:
            continue
        if f[0] == "cap":
            cap = int(f[1])
        elif f[0] == "mark":
            mark = int(f[1])
        elif f[0] == "pull":
            msgs.append(("pull", int(f[1]), None))
        elif f[0] == "new":
            px = None if f[4] == "-" else int(f[4])
            shw = None if f[6] == "-" else int(f[6])
            trp = None if f[8] == "-" else int(f[8])
            msgs.append(("new", int(f[1]),
                         Rec(int(f[1]), int(f[2]), f[3], px, int(f[5]), shw, f[7], trp)))
        else:
            raise ValueError(raw)
    return cap, mark, msgs


def other(side):
    return "s" if side == "b" else "b"


def best(S, side):
    pool = S.bk[side]
    if not pool:
        return None
    return min(r.px for r in pool) if side == "s" else max(r.px for r in pool)


def front(S, side, px):
    pick = None
    for r in S.bk[side]:
        if r.px == px and (pick is None or r.seq < pick.seq):
            pick = r
    return pick


def crosses(o, px):
    if o.px is None:
        return True
    return px <= o.px if o.side == "b" else px >= o.px


def check(S):
    hit = sorted(S.pen.fired(S.last), key=lambda a: a.oid)
    for a in hit:
        S.pen.gone(a)
        S.row("trp", a.oid)
        S.pend.append(a)
    return hit


def note(trail, item):
    if trail is not None:
        trail.append(item)


def walk(S, o, trail=None):
    side = other(o.side)
    while o.rem > 0:
        px = best(S, side)
        if px is None:
            return
        if not crosses(o, px):
            return
        if abs(px - S.last) > S.cap:
            return
        r = front(S, side, px)
        if r.hand == o.hand:
            S.bk[side].remove(r)
            note(trail, ("gone", side, r))
            S.row("pul", r.oid, "same")
            continue
        q = min(o.rem, r.shn)
        S.row("trd", o.oid, r.oid, px, q)
        o.rem -= q
        r.rem -= q
        r.shn -= q
        note(trail, ("fill", r, q))
        note(trail, ("last", S.last, None))
        S.last = px
        note(trail, ("trip", check(S), None))
        if r.rem == 0:
            S.bk[side].remove(r)
            note(trail, ("gone", side, r))
        elif r.shn == 0:
            note(trail, ("seq", r, r.seq, r.shn))
            note(trail, ("cnt", S.seq, None))
            r.shn = r.rem if r.shw is None else min(r.shw, r.rem)
            S.seq += 1
            r.seq = S.seq
            S.row("shw", r.oid, r.shn)


def rewind(S, o, trail):
    for item in reversed(trail):
        kind = item[0]
        if kind == "fill":
            r, q = item[1], item[2]
            r.rem += q
            r.shn += q
            o.rem += q
        elif kind == "gone":
            S.bk[item[1]].append(item[2])
        elif kind == "seq":
            item[1].seq = item[2]
            item[1].shn = item[3]
        elif kind == "cnt":
            S.seq = item[1]
        elif kind == "last":
            S.last = item[1]
        elif kind == "trip":
            for a in item[1]:
                S.pen.add(a)


def park(S, o):
    S.bk[o.side].append(o)
    S.seq += 1
    o.seq = S.seq
    o.shn = o.rem if o.shw is None else min(o.shw, o.rem)
    S.row("rst", o.oid, o.px, o.shn)


def submit(S, o):
    if o.tif == "whole":
        trail = []
        held = len(S.pend)
        said = len(S.rows)
        walk(S, o, trail)
        if o.rem > 0:
            del S.rows[said:]
            while len(S.pend) > held:
                S.pend.pop()
            rewind(S, o, trail)
            S.row("pul", o.oid, "whole")
        return
    walk(S, o)
    if o.rem > 0:
        if o.px is None:
            S.row("pul", o.oid, "mkt")
        elif o.tif == "part":
            S.row("pul", o.oid, "part")
        else:
            park(S, o)


def solve(text):
    cap, mark, msgs = parse(text)
    S = State(cap, mark)
    for kind, oid, rec in msgs:
        if kind == "pull":
            held = S.pen.has(oid)
            if held is not None:
                S.pen.gone(held)
                S.row("pul", oid, "user")
                continue
            hits = [r for side in ("b", "s") for r in S.bk[side] if r.oid == oid]
            if hits:
                S.bk[hits[0].side].remove(hits[0])
                S.row("pul", oid, "user")
            continue
        if rec.trp is not None:
            S.pen.add(rec)
            S.row("arm", rec.oid)
            continue
        submit(S, rec)
        while S.pend:
            nxt = S.pend.pop(0)
            nxt.trp = None
            submit(S, nxt)
    for side in ("b", "s"):
        pool = sorted(S.bk[side],
                      key=lambda r: ((-r.px if side == "b" else r.px), r.seq))
        for r in pool:
            S.row("bk", side, r.px, r.oid, r.shn, r.rem)
    for a in S.pen.rest():
        S.row("am", a.oid)
    return S.rows
