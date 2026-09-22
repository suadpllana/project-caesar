"""A correct variant with everything in one module. Never ships.

Written from the contract, not from the reference: a Fenwick tree over each row of children,
contributions pushed up eagerly with point updates, tops recomputed on every call without a
memo, the band found by recursion over the rows crossing the top strip, and the settle written
as a fixed four-step loop that records every pass and takes the least offset at the end.
"""


class Fen:
    __slots__ = ("n", "t")

    def __init__(self, vals):
        n = len(vals)
        t = [0] * (n + 1)
        for i in range(1, n + 1):
            t[i] += vals[i - 1]
            j = i + (i & -i)
            if j <= n:
                t[j] += t[i]
        self.n = n
        self.t = t

    def add(self, i, d):
        i += 1
        while i <= self.n:
            self.t[i] += d
            i += i & -i

    def pre(self, i):
        s = 0
        while i > 0:
            s += self.t[i]
            i -= i & -i
        return s

    def past(self, x):
        pos, rem = 0, x
        step = 1 << self.n.bit_length()
        while step:
            nxt = pos + step
            if nxt <= self.n and self.t[nxt] <= rem:
                pos = nxt
                rem -= self.t[nxt]
            step >>= 1
        return pos


class Row:
    """The children of one box (or of the document) as the layout sees them."""

    __slots__ = ("fen", "ix", "pins")

    def __init__(self, kids):
        self.fen = Fen([k.xc for k in kids])
        self.ix = {k: i for i, k in enumerate(kids)}
        self.pins = [i for i, k in enumerate(kids) if k.pin is not None]


def kids_of(v, owner):
    return v.kids if owner is None else owner.kids


def row_of(v, owner):
    got = v.xrow if owner is None else owner.xrow
    if got is None:
        got = Row(kids_of(v, owner))
        if owner is None:
            v.xrow = got
        else:
            owner.xrow = got
    return got


def measure(b):
    total = 0
    for k in b.kids:
        total += measure(k)
    b.xk = total
    b.xh = b.own + (0 if b.shut else total)
    b.xc = 0 if b.lift else b.xh
    b.xrow = None
    return b.xc


def start(v):
    v.xtotal = 0
    for b in v.kids:
        v.xtotal += measure(b)
    v.xrow = None
    v.xmax = max([b.pin for b in v.box.values() if b.pin is not None] or [0])
    v.xchain = None


def carry(v, owner, d):
    """A child of owner counts d more; walk the change up while it changes anything."""
    while owner is not None:
        owner.xk += d
        owner.xh = owner.own + (0 if owner.shut else owner.xk)
        new = 0 if owner.lift else owner.xh
        d, owner.xc = new - owner.xc, new
        if d == 0:
            return
        up = owner.par
        r = v.xrow if up is None else up.xrow
        if r is not None:
            r.fen.add(r.ix[owner], d)
        owner = up
    v.xtotal += d


def redo(v, b):
    b.xh = b.own + (0 if b.shut else b.xk)
    new = 0 if b.lift else b.xh
    d, b.xc = new - b.xc, new
    if d:
        r = v.xrow if b.par is None else b.par.xrow
        if r is not None:
            r.fen.add(r.ix[b], d)
        carry(v, b.par, d)


def forget_row(v, owner):
    if owner is None:
        v.xrow = None
    else:
        owner.xrow = None


def replay(v):
    for kind, b, arg in v.log:
        if kind == "to":
            continue
        if kind == "add":
            b.xk, b.xh, b.xc, b.xrow = 0, b.own, 0, None
            forget_row(v, b.par)
            if b.pin is not None:
                v.xmax = max(v.xmax, b.pin)
            redo(v, b)
        elif kind == "drop":
            forget_row(v, b.par)
            d, b.xc = -b.xc, 0
            if d:
                carry(v, b.par, d)
        elif kind in ("pin", "unpin"):
            if b.pin is not None:
                v.xmax = max(v.xmax, b.pin)
            forget_row(v, b.par)
        else:
            redo(v, b)


def top(v, b):
    y = 0
    x = b
    while x is not None:
        owner = x.par
        r = row_of(v, owner)
        y += r.fen.pre(r.ix[x])
        if owner is not None:
            y += owner.own
        x = owner
    return y


def start_of(v, owner):
    return 0 if owner is None else top(v, owner) + owner.own


def shows(b):
    if b.gone or b.lift:
        return False
    p = b.par
    while p is not None:
        if p.lift or p.shut:
            return False
        p = p.par
    return True


def drawn_at(v, b, s):
    if b.pin is None or b.xh <= 0:
        return None
    end = v.xtotal if b.par is None else top(v, b.par) + b.par.xh
    r = min(s + b.pin, end - b.xh)
    return r if r > top(v, b) else None


def lowest_edge(v, s):
    hi = s + v.xmax

    def walk(owner):
        kids = kids_of(v, owner)
        r = row_of(v, owner)
        base = start_of(v, owner)
        best = 0
        for i in r.pins:
            k = kids[i]
            if base + r.fen.pre(i) >= hi:
                break
            if k.lift:
                continue
            at = drawn_at(v, k, s)
            if at is not None:
                best = max(best, at + k.xh - s)
        i = r.fen.past(s - base)
        while i < len(kids):
            k = kids[i]
            if base + r.fen.pre(i) >= hi:
                break
            if k.xc > 0 and not k.shut:
                best = max(best, walk(k))
            i += 1
        return best

    return walk(None)


def choose(v, s, band):
    u, w = s + band, s + v.vh
    if u >= w:
        return None

    def look(owner):
        kids = kids_of(v, owner)
        r = row_of(v, owner)
        base = start_of(v, owner)
        i = r.fen.past(u - base)
        while i < len(kids):
            k = kids[i]
            y = base + r.fen.pre(i)
            if y >= w:
                return None
            i += 1
            if k.xc == 0 or k.live or drawn_at(v, k, s) is not None:
                continue
            if y >= u and y + k.xh <= w:
                return k
            if not k.shut:
                inner = look(k)
                if inner is not None:
                    return inner
            return k
        return None

    return look(None)


def before(v):
    s = v.s
    band = lowest_edge(v, s)
    got = choose(v, s, band)
    if got is None:
        v.xchain = None
        return
    line = s + band
    v.xchain = []
    x = got
    while x is not None:
        v.xchain.append((x, top(v, x) - line))
        x = x.par


def fit(v, s):
    return max(0, min(s, max(0, v.xtotal - v.vh)))


def ok(v, x, s):
    if not shows(x) or x.xh <= 0:
        return False
    y = x
    while y is not None:
        if drawn_at(v, y, s) is not None:
            return False
        y = y.par
    return True


def after(v):
    scroll = None
    quiet = False
    for kind, b, arg in v.log:
        if kind == "to":
            scroll = arg
            continue
        y = b
        while y is not None:
            if y.live:
                quiet = True
            y = y.par
    replay(v)
    if scroll is not None:
        return fit(v, scroll), "off scroll"
    if quiet:
        return fit(v, v.s), "off live"
    if v.xchain is None:
        return fit(v, v.s), "none"
    at = v.s
    tried = []
    for k in range(4):
        band = lowest_edge(v, at)
        pick = next(((x, d) for x, d in v.xchain if ok(v, x, at)), None)
        if pick is None:
            return fit(v, at), "none"
        x, d = pick
        nxt = fit(v, top(v, x) - d - band)
        if nxt == at:
            return at, x.id
        tried.append((nxt, k, x))
        at = nxt
    off, _k, x = min(tried, key=lambda t: (t[0], t[1]))
    return off, x.id
