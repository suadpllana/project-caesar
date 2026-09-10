class Buck:
    def __init__(self):
        self.ks = []
        self.es = []
        self.ss = []
        self.ds = []
        self.n = 0
        self.sn = {}


def hold(tab, buck):
    b = tab.buck.get(buck)
    if b is None:
        b = tab.buck[buck] = Buck()
    return b


def rows(tab, buck):
    b = tab.buck.get(buck)
    if b is None:
        return 0
    n = 0
    for t in range(len(b.ks)):
        n += b.es[t] - b.ks[t] + 1
    return n


def at(tab, buck, key):
    b = tab.buck.get(buck)
    if b is None:
        return None
    for t in range(len(b.ks)):
        if b.ks[t] <= key <= b.es[t]:
            return b.ds[t]
    return None


def window(b, lo, hi):
    n = len(b.ks)
    i = 0
    while i < n and b.es[i] < lo:
        i += 1
    j = i
    while j < n and b.ks[j] <= hi:
        j += 1
    return i, j


def splice(b, i, j, ks, es, ss, ds, jr):
    jr.append(("sp", b, i, len(ks), b.ks[i:j], b.es[i:j], b.ss[i:j], b.ds[i:j]))
    b.ks[i:j] = ks
    b.es[i:j] = es
    b.ss[i:j] = ss
    b.ds[i:j] = ds


def retag(b, t, sid, jr):
    jr.append(("dt", b, t, b.ds[t]))
    b.ds[t] = sid


def bump(b, sid, d, jr):
    old = b.sn.get(sid, 0)
    jr.append(("sn", b, sid, old))
    now = old + d
    if now:
        b.sn[sid] = now
        return False
    b.sn.pop(sid, None)
    return old != 0


def total(b, d, jr):
    jr.append(("bn", b, b.n))
    b.n += d


def sow(tab, buck, lo, hi, stamp, sid, jr):
    b = hold(tab, buck)
    i = 0
    n = len(b.ks)
    while i < n and b.ks[i] <= lo:
        i += 1
    splice(b, i, i, [lo], [hi], [stamp], [sid], jr)
    bump(b, sid, hi - lo + 1, jr)
    total(b, hi - lo + 1, jr)


def undo(jr):
    for e in reversed(jr):
        kind = e[0]
        if kind == "sp":
            _, b, i, n, ks, es, ss, ds = e
            b.ks[i:i + n] = ks
            b.es[i:i + n] = es
            b.ss[i:i + n] = ss
            b.ds[i:i + n] = ds
        elif kind == "sn":
            _, b, sid, old = e
            if old:
                b.sn[sid] = old
            else:
                b.sn.pop(sid, None)
        elif kind == "dt":
            _, b, t, sid = e
            b.ds[t] = sid
        else:
            _, b, old = e
            b.n = old
    del jr[:]
