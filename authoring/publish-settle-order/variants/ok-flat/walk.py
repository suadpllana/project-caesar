import bisect
from fractions import Fraction

from reg import hold, order, say, tab


def _st(h):
    st = getattr(h, "st", None)
    if st is None:
        st = h.st = {"idx": {}, "den": {}, "home": {}, "owed": {}, "loose": [], "seq": [],
                     "top": 0, "scopes": 0, "busy": set()}
    return st


def _names(r):
    return dict.fromkeys(p[0] for p in r.pubs)


def _hard(r):
    return dict.fromkeys(o for o, kind in r.needs if kind)


def _bucket(st, den, sym):
    return st["idx"].setdefault((den, sym), [])


def _drop(lst, key):
    i = bisect.bisect_left(lst, (key,))
    if i < len(lst) and lst[i][0] == key:
        del lst[i]


def bring(h, name, wide, out):
    st = _st(h)
    r = tab.get(h, name)
    if r.live:
        was = st["den"].get(r.name)
        if wide and was is not None:
            st["den"][r.name] = None
            for sym in _names(r):
                _drop(_bucket(st, was, sym), r.at)
                bisect.insort(_bucket(st, None, sym), (r.at, r.name))
        hold.take(h, name)
        return
    if wide:
        den = None
    else:
        st["scopes"] += 1
        den = st["scopes"]
    _up(h, r, den, None, out)
    hold.take(h, name)


def _key(st, before):
    if before is None:
        st["top"] += 1
        return Fraction(st["top"])
    seq = st["seq"]
    i = bisect.bisect_left(seq, (before.at,))
    low = seq[i - 1][0] if i > 0 else before.at - 1
    return (low + before.at) / 2


def _up(h, r, den, before, out):
    st = _st(h)
    busy = st["busy"]
    busy.add(r.name)
    for other, _kind in r.needs:
        dr = tab.get(h, other)
        if dr.live or dr.name in busy:
            continue
        _up(h, dr, den, before, out)
    r.at = _key(st, before)
    bisect.insort(st["seq"], (r.at, r.name))
    if before is None:
        order.add(h, r)
    else:
        order.put(h, r, before)
    r.live = True
    r.uses = {}
    r.ties = []
    st["den"][r.name] = den
    st["home"][r.name] = den
    for sym in _names(r):
        bisect.insort(_bucket(st, den, sym), (r.at, r.name))
    for other in _hard(r):
        st["owed"][other] = st["owed"].get(other, 0) + 1
    if not wanted(h, r):
        bisect.insort(st["loose"], (-r.at, r.name))
    say.up(out, r.name)
    for sym in r.boots:
        reach(h, r, sym, out)
    busy.discard(r.name)


def keys(h, caller):
    mine = _st(h)["home"].get(caller.name)
    return (None,) if mine is None else (None, mine)


def find(h, caller, sym):
    st = _st(h)
    best = None
    for key in keys(h, caller):
        lst = st["idx"].get((key, sym))
        if lst and (best is None or lst[0][0] < best[0]):
            best = lst[0]
    return None if best is None else h.units[best[1]]


def lazy(h, caller, sym, out):
    st = _st(h)
    for name in h.autos:
        r = h.units[name]
        if r.live or name in st["busy"] or sym not in _names(r):
            continue
        _up(h, r, st["home"].get(caller.name), caller, out)
        caller.ties.append(name)
        st["owed"][name] = st["owed"].get(name, 0) + 1
        return r
    return None


def reach(h, r, sym, out):
    if not r.live:
        return
    u = r.uses.get(sym)
    if u is None:
        t = find(h, r, sym)
        if t is None and lazy(h, r, sym, out) is not None:
            t = find(h, r, sym)
        if t is None:
            say.miss(out, r.name, sym)
            return
        r.uses[sym] = (t, t.at)
        say.ran(out, r.name, sym, t.name)
        return
    t, at = u
    if t.live and t.at == at:
        say.ran(out, r.name, sym, t.name)
    else:
        say.dead(out, r.name, sym)


def wanted(h, r):
    return hold.held(h, r.name) > 0 or _st(h)["owed"].get(r.name, 0) > 0


def let(h, name, out):
    st = _st(h)
    r = tab.get(h, name)
    if not r.live or hold.held(h, name) <= 0:
        return
    hold.give(h, name)
    bisect.insort(st["loose"], (-r.at, r.name))
    while st["loose"]:
        key, who = st["loose"].pop(0)
        go = h.units[who]
        if not go.live or go.at != -key or wanted(h, go):
            continue
        for other in list(_hard(go)) + go.ties:
            left = st["owed"].get(other, 0) - 1
            st["owed"][other] = left
            if left < 1:
                rec = h.units.get(other)
                if rec is not None and rec.live:
                    bisect.insort(st["loose"], (-rec.at, rec.name))
        go.ties = []
        go.live = False
        _drop(st["seq"], go.at)
        order.drop(h, go)
        for sym in _names(go):
            _drop(_bucket(st, st["den"].get(go.name), sym), go.at)
        say.down(out, go.name)
