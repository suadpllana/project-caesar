from hold import mark


class Req(object):
    __slots__ = ("tx", "kn", "ask", "seq")

    def __init__(self, tx, kn, ask, seq):
        self.tx = tx
        self.kn = kn
        self.ask = ask
        self.seq = seq


class Item(object):
    __slots__ = ("name", "stack", "first", "eff", "by", "pend")

    def __init__(self, name):
        self.name = name
        self.stack = {}
        self.first = {}
        self.eff = {}
        self.by = {}
        self.pend = []


def _move(by, t, was, now):
    if was is not None:
        s = by.get(was)
        if s is not None:
            s.discard(t)
            if not s:
                del by[was]
    if now is not None:
        by.setdefault(now, set()).add(t)


def add(it, t, ask, now):
    st = it.stack.get(t)
    if st is None:
        it.stack[t] = [ask]
        it.first[t] = now
        it.eff[t] = ask
        _move(it.by, t, None, ask)
    else:
        st.append(ask)
        was = it.eff[t]
        got = mark.join2(was, ask)
        if got != was:
            _move(it.by, t, was, got)
            it.eff[t] = got
    return it.eff[t]


def sub(it, t):
    st = it.stack[t]
    st.pop()
    was = it.eff[t]
    if st:
        got = mark.join(st)
        if got != was:
            _move(it.by, t, was, got)
            it.eff[t] = got
        return got
    _move(it.by, t, was, None)
    del it.stack[t]
    del it.first[t]
    del it.eff[t]
    return None


def wipe(it, t):
    if t in it.stack:
        _move(it.by, t, it.eff[t], None)
        del it.stack[t]
        del it.first[t]
        del it.eff[t]


def sweep(it, drop=None):
    """Raises first in hold order, then first-time claims while nothing was passed over.
    The holder index is read through an overlay so the item itself is never touched."""
    over = {}

    def who(m):
        got = over.get(m)
        return it.by.get(m, ()) if got is None else got

    def stands(want, own):
        for bad in mark.CONF[want]:
            s = who(bad)
            if not s:
                continue
            n = len(s)
            if own in s:
                n -= 1
            if drop is not None and drop in s:
                n -= 1
            if n > 0:
                return False
        return True

    def shift(t, was, now):
        if was is not None:
            if was not in over:
                over[was] = set(it.by.get(was, ()))
            over[was].discard(t)
        if now not in over:
            over[now] = set(it.by.get(now, ()))
        over[now].add(t)

    eff = it.eff
    cur = {}
    ups = [r for r in it.pend if r.tx in eff and r.tx != drop]
    if len(ups) > 1:
        ups.sort(key=lambda r: it.first[r.tx])
    got = []
    stuck = False
    for r in ups:
        held = cur.get(r.tx) or eff[r.tx]
        want = mark.join2(held, r.ask)
        if stands(want, r.tx):
            shift(r.tx, held, want)
            cur[r.tx] = want
            got.append(r)
        else:
            stuck = True
    if not stuck:
        for r in it.pend:
            if r.tx == drop or r.tx in eff:
                continue
            if stands(r.ask, r.tx):
                shift(r.tx, None, r.ask)
                got.append(r)
            else:
                break
    return got
