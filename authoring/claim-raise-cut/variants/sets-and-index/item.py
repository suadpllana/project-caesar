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


def _put(by, m, t):
    by.setdefault(m, set()).add(t)


def _take(by, m, t):
    who = by.get(m)
    if who is not None:
        who.discard(t)
        if not who:
            del by[m]


def add(it, t, ask, now):
    st = it.stack.get(t)
    if st is None:
        it.stack[t] = [ask]
        it.first[t] = now
        it.eff[t] = ask
        _put(it.by, ask, t)
    else:
        st.append(ask)
        was = it.eff[t]
        got = mark.join2(was, ask)
        if got != was:
            _take(it.by, was, t)
            _put(it.by, got, t)
            it.eff[t] = got
    return it.eff[t]


def sub(it, t):
    st = it.stack[t]
    st.pop()
    was = it.eff[t]
    _take(it.by, was, t)
    if st:
        got = mark.join(st)
        it.eff[t] = got
        _put(it.by, got, t)
        return got
    del it.stack[t]
    del it.first[t]
    del it.eff[t]
    return None


def wipe(it, t):
    if t in it.stack:
        _take(it.by, it.eff[t], t)
        del it.stack[t]
        del it.first[t]
        del it.eff[t]


def sweep(it, drop=None):
    moved = {}

    def seen(m):
        got = moved.get(m)
        return it.by.get(m, ()) if got is None else got

    def stands(want, own):
        for bad in mark.CONF[want]:
            who = seen(bad)
            if not who:
                continue
            n = len(who)
            if own in who:
                n -= 1
            if drop is not None and drop in who:
                n -= 1
            if n > 0:
                return False
        return True

    def shift(m, t, gone):
        cur = moved.get(m)
        if cur is None:
            cur = moved[m] = set(it.by.get(m, ()))
        if gone:
            cur.discard(t)
        else:
            cur.add(t)

    ups = [r for r in it.pend if r.tx in it.eff and r.tx != drop]
    if len(ups) > 1:
        ups.sort(key=lambda r: it.first[r.tx])
    got = []
    stuck = False
    for r in ups:
        cur = it.eff[r.tx]
        want = mark.join2(cur, r.ask)
        if stands(want, r.tx):
            shift(cur, r.tx, True)
            shift(want, r.tx, False)
            got.append(r)
        else:
            stuck = True
    if not stuck:
        for r in it.pend:
            if r.tx == drop or r.tx in it.eff:
                continue
            if stands(r.ask, None):
                shift(r.ask, r.tx, False)
                got.append(r)
            else:
                break
    return got
