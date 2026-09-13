from pan import gues, mtr


class Nd:
    __slots__ = ("pri", "rid", "ln", "hm", "sz", "ms", "uc", "l", "r", "up")

    def __init__(self, pri, rid, ln):
        self.pri = pri
        self.rid = rid
        self.ln = ln
        self.hm = None
        self.sz = 1
        self.ms = 0
        self.uc = 1
        self.l = None
        self.r = None
        self.up = None


class Pan:
    __slots__ = ("root", "seed", "ms", "uc", "n", "ix", "w", "top", "anc", "dy", "made")

    def __init__(self):
        self.root = None
        self.seed = 0x9E3779B1
        self.ms = 0
        self.uc = 0
        self.n = 0
        self.ix = {}
        self.w = mtr.W0
        self.top = 0
        self.anc = None
        self.dy = 0
        self.made = 0


def new():
    return Pan()


def draw(p):
    p.seed = (p.seed * 1103515245 + 12345) & 0x3FFFFFFF
    return p.seed


def size(x):
    return x.sz if x else 0


def pull(x):
    s = 1
    m = x.hm if x.hm is not None else 0
    u = 0 if x.hm is not None else 1
    for k in (x.l, x.r):
        if k:
            s += k.sz
            m += k.ms
            u += k.uc
    x.sz = s
    x.ms = m
    x.uc = u


def fix(x):
    while x:
        pull(x)
        x = x.up


def held(p, x):
    return x.hm is not None


def hgt(p, x, e):
    return x.hm if x.hm is not None else e


def sub(x, e):
    return (x.ms + x.uc * e) if x else 0


def full(p):
    return p.ms + p.uc * gues.hei(p)


def edge(p):
    t = full(p)
    return t - mtr.VIEW if t > mtr.VIEW else 0


def row(p, rid):
    return p.ix.get(rid)


def swing(p, x):
    q = x.up
    g = q.up
    if q.l is x:
        q.l = x.r
        if x.r:
            x.r.up = q
        x.r = q
    else:
        q.r = x.l
        if x.l:
            x.l.up = q
        x.l = q
    q.up = x
    x.up = g
    if g:
        if g.l is q:
            g.l = x
        else:
            g.r = x
    else:
        p.root = x
    pull(q)
    pull(x)


def put(p, k, nd):
    if p.root is None:
        p.root = nd
    else:
        x = p.root
        while True:
            left = size(x.l)
            if k <= left:
                if x.l is None:
                    x.l = nd
                    nd.up = x
                    break
                x = x.l
            else:
                k -= left + 1
                if x.r is None:
                    x.r = nd
                    nd.up = x
                    break
                x = x.r
    fix(nd.up)
    while nd.up and nd.pri > nd.up.pri:
        swing(p, nd)
    p.n += 1
    if nd.hm is None:
        p.uc += 1
    else:
        p.ms += nd.hm
    p.ix[nd.rid] = nd


def drop(p, nd):
    while nd.l or nd.r:
        if nd.l is None:
            swing(p, nd.r)
        elif nd.r is None:
            swing(p, nd.l)
        elif nd.l.pri > nd.r.pri:
            swing(p, nd.l)
        else:
            swing(p, nd.r)
    q = nd.up
    if q is None:
        p.root = None
    elif q.l is nd:
        q.l = None
    else:
        q.r = None
    nd.up = None
    fix(q)
    p.n -= 1
    if nd.hm is None:
        p.uc -= 1
    else:
        p.ms -= nd.hm
    p.ix.pop(nd.rid, None)


def off(p, nd):
    e = gues.hei(p)
    acc = sub(nd.l, e)
    x = nd
    while x.up:
        if x.up.r is x:
            acc += sub(x.up.l, e) + hgt(p, x.up, e)
        x = x.up
    return acc


def rank(p, nd):
    k = size(nd.l)
    x = nd
    while x.up:
        if x.up.r is x:
            k += size(x.up.l) + 1
        x = x.up
    return k


def kth(p, k):
    x = p.root
    while x:
        left = size(x.l)
        if k < left:
            x = x.l
        elif k == left:
            return x
        else:
            k -= left + 1
            x = x.r
    return None


def hit(p):
    e = gues.hei(p)
    acc = 0
    x = p.root
    while x:
        hl = sub(x.l, e)
        if acc + hl + hgt(p, x, e) > p.top:
            if acc + hl > p.top:
                x = x.l
            else:
                return x, acc + hl
        else:
            acc += hl + hgt(p, x, e)
            x = x.r
    return None, acc


def after(p, nd):
    if nd.r:
        x = nd.r
        while x.l:
            x = x.l
        return x
    x = nd
    while x.up and x.up.r is x:
        x = x.up
    return x.up


def down(p, nd, acc):
    e = gues.hei(p)
    stop = p.top + mtr.VIEW
    x = nd
    while x and acc < stop:
        yield x
        acc += hgt(p, x, e)
        x = after(p, x)


def mark(p, nd):
    h = mtr.high(nd.ln, p.w)
    nd.hm = h
    p.ms += h
    p.uc -= 1
    fix(nd)


def wipe(p, nd):
    if nd.hm is None:
        return
    p.ms -= nd.hm
    p.uc += 1
    nd.hm = None
    fix(nd)


def fresh(p):
    seen = []
    stack = [p.root] if p.root else []
    while stack:
        nd = stack.pop()
        nd.hm = None
        seen.append(nd)
        if nd.l:
            stack.append(nd.l)
        if nd.r:
            stack.append(nd.r)
    for nd in reversed(seen):
        pull(nd)
    p.ms = 0
    p.uc = p.n
