from hold import mark


class Req(object):
    __slots__ = ("tx", "kn", "ask", "seq")

    def __init__(self, tx, kn, ask, seq):
        self.tx = tx
        self.kn = kn
        self.ask = ask
        self.seq = seq


class Item(object):
    __slots__ = ("name", "stack", "first", "eff", "cnt", "pend")

    def __init__(self, name):
        self.name = name
        self.stack = {}
        self.first = {}
        self.eff = {}
        self.cnt = {}
        self.pend = []


def _bump(cnt, m, d):
    n = cnt.get(m, 0) + d
    if n:
        cnt[m] = n
    else:
        cnt.pop(m, None)


def stands(cnt, want, own):
    for n in mark.CONF[want]:
        c = cnt.get(n, 0)
        if own == n:
            c -= 1
        if c > 0:
            return False
    return True


def add(it, t, ask, now):
    st = it.stack.get(t)
    if st is None:
        it.stack[t] = [ask]
        it.first[t] = now
        it.eff[t] = ask
        _bump(it.cnt, ask, 1)
    else:
        st.append(ask)
        was = it.eff[t]
        got = mark.join2(was, ask)
        if got != was:
            _bump(it.cnt, was, -1)
            _bump(it.cnt, got, 1)
            it.eff[t] = got
    return it.eff[t]


def sub(it, t):
    st = it.stack[t]
    st.pop()
    was = it.eff[t]
    if st:
        got = mark.join(st)
        if got != was:
            _bump(it.cnt, was, -1)
            _bump(it.cnt, got, 1)
            it.eff[t] = got
        return got
    _bump(it.cnt, was, -1)
    del it.stack[t]
    del it.first[t]
    del it.eff[t]
    return None


def wipe(it, t):
    if t in it.stack:
        _bump(it.cnt, it.eff[t], -1)
        del it.stack[t]
        del it.first[t]
        del it.eff[t]


def sweep(it, drop=None):
    eff = it.eff
    cnt = dict(it.cnt)
    if drop is not None and drop in eff:
        _bump(cnt, eff[drop], -1)
    ups = [r for r in it.pend if r.tx in eff and r.tx != drop]
    got = []
    stuck = False
    for r in ups:
        cur = eff[r.tx]
        want = mark.join2(cur, r.ask)
        if stands(cnt, want, cur):
            _bump(cnt, cur, -1)
            _bump(cnt, want, 1)
            got.append(r)
        else:
            stuck = True
    if not stuck:
        for r in it.pend:
            if r.tx == drop or r.tx in eff:
                continue
            if stands(cnt, r.ask, None):
                _bump(cnt, r.ask, 1)
                got.append(r)
            else:
                break
    return got
