from eng import back, pick
from eng.pool import Blk, Pool, keys


class Ghost(object):
    __slots__ = ("idx", "toks", "plen", "have", "seen")

    def __init__(self, r):
        self.idx = r.idx
        self.toks = r.toks
        self.plen = r.plen
        self.have = r.have
        self.seen = r.seen


def shadow(pool):
    p = Pool(pool.cap, pool.span)
    p.priv = pool.priv
    p.born = pool.born
    for k in sorted(pool.blk):
        b = pool.blk[k]
        n = Blk(b.born)
        n.refs = b.refs
        n.touch = b.touch
        p.blk[k] = n
    return p


def drop(p, g, span):
    for k in keys(g.toks, span, g.have):
        p.give(k)
    if g.have % span:
        p.free()


def ok(w, cand):
    p = shadow(w.pool)
    order = [Ghost(r) for r in w.dec]
    live = list(order)
    for g in order:
        if g not in live:
            continue
        lost = False
        while g.have % w.span == 0 and not p.hold():
            v = pick.victim(w, live)
            if v is None:
                return False
            drop(p, v, w.span)
            live.remove(v)
            if v is g:
                lost = True
                break
        if lost:
            continue
        g.have += 1
        if g.have % w.span == 0:
            p.free()
            if not p.take(keys(g.toks, w.span, g.have)[-1], w.t):
                return False
    for g in list(live):
        if g.have >= len(g.toks):
            drop(p, g, w.span)
            live.remove(g)
    spend = 0
    for r in w.joining + [cand]:
        tgt = r.plen if r.have == 0 else r.have
        spend += tgt - back.at(p, w.span, r)
        for k in keys(r.toks, w.span, tgt):
            if not p.take(k, w.t):
                return False
        if tgt % w.span:
            if not p.hold():
                return False
    return spend <= w.left
