from eng import back, pick
from eng.pool import Blk, Pool, keys


class Stand(object):
    __slots__ = ("idx", "toks", "plen", "have", "seen")

    def __init__(self, rq):
        self.idx = rq.idx
        self.toks = rq.toks
        self.plen = rq.plen
        self.have = rq.have
        self.seen = rq.seen


def mirrorpool(pool):
    sp = Pool(pool.cap, pool.span)
    sp.priv = pool.priv
    sp.born = pool.born
    for tagged in pool.blk:
        b = pool.blk[tagged]
        clone = Blk(b.born)
        clone.refs = b.refs
        clone.touch = b.touch
        sp.blk[tagged] = clone
    return sp


def letgo(sp, st, span):
    for tagged in keys(st.toks, span, st.have):
        sp.give(tagged)
    if st.have % span:
        sp.free()


def ok(w, wanting):
    sp = mirrorpool(w.pool)
    order = [Stand(rq) for rq in w.dec]
    standing = list(order)
    for st in order:
        if st not in standing:
            continue
        evicted = False
        while st.have % w.span == 0 and not sp.hold():
            v = pick.victim(w, standing)
            if v is None:
                return False
            letgo(sp, v, w.span)
            standing.remove(v)
            if v is st:
                evicted = True
                break
        if evicted:
            continue
        st.have += 1
        if st.have % w.span == 0:
            sp.free()
            if not sp.take(keys(st.toks, w.span, st.have)[-1], w.t):
                return False
    for st in list(standing):
        if st.have >= len(st.toks):
            letgo(sp, st, w.span)
            standing.remove(st)
    outlay = 0
    for rq in w.joining + [wanting]:
        aim = rq.plen if rq.have == 0 else rq.have
        outlay += aim - back.at(sp, w.span, rq)
        for tagged in keys(rq.toks, w.span, aim):
            if not sp.take(tagged, w.t):
                return False
        if aim % w.span:
            if not sp.hold():
                return False
    return outlay <= w.left
