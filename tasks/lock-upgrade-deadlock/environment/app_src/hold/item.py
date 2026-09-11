from hold import mark


class Req(object):
    __slots__ = ("tx", "kn", "ask", "seq")

    def __init__(self, tx, kn, ask, seq):
        self.tx = tx
        self.kn = kn
        self.ask = ask
        self.seq = seq


class Item(object):
    __slots__ = ("name", "stack", "first", "eff", "pend")

    def __init__(self, name):
        self.name = name
        self.stack = {}
        self.first = {}
        self.eff = {}
        self.pend = []


def want(it, r):
    st = it.stack.get(r.tx)
    return r.ask if st is None else mark.join(st + [r.ask])


def add(it, t, ask, now):
    st = it.stack.get(t)
    if st is None:
        it.stack[t] = [ask]
        it.first[t] = now
        it.eff[t] = ask
    else:
        st.append(ask)
        it.eff[t] = mark.join(st)
    return it.eff[t]


def sub(it, t):
    it.stack.pop(t, None)
    it.first.pop(t, None)
    it.eff.pop(t, None)
    return None


def wipe(it, t):
    it.stack.pop(t, None)
    it.first.pop(t, None)
    it.eff.pop(t, None)


def sweep(it):
    got = []
    seen = dict(it.eff)
    for r in it.pend:
        w = want(it, r)
        g = mark.join(seen.values()) if seen else None
        if g is None or mark.fits(w, g):
            seen[r.tx] = w
            got.append(r)
        else:
            break
    return got
