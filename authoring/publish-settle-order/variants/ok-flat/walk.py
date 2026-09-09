import heapq

from reg import hold, order, say, tab


def _st(h):
    st = getattr(h, "st", None)
    if st is None:
        st = h.st = {"idx": {}, "den": {}, "owed": {}, "loose": [], "n": 0, "scopes": 0}
    return st


def _names(r):
    return dict.fromkeys(p[0] for p in r.pubs)


def _hard(r):
    return dict.fromkeys(o for o, kind in r.needs if kind)


def bring(h, name, wide, out):
    st = _st(h)
    r = tab.get(h, name)
    if r.live:
        was = st["den"].get(r.name)
        if wide and was is not None:
            st["den"][r.name] = None
            for sym in _names(r):
                st["idx"][(was, sym)] = [x for x in st["idx"].get((was, sym), []) if x is not r]
                pub = st["idx"].setdefault((None, sym), [])
                pub.append(r)
                pub.sort(key=lambda x: x.at)
        hold.take(h, name)
        return
    if wide:
        den = None
    else:
        st["scopes"] += 1
        den = st["scopes"]
    _up(h, r, den, set(), out)
    hold.take(h, name)


def _up(h, r, den, busy, out):
    st = _st(h)
    busy.add(r.name)
    for other, _kind in r.needs:
        dr = tab.get(h, other)
        if dr.live or dr.name in busy:
            continue
        _up(h, dr, den, busy, out)
    st["n"] += 1
    r.at = st["n"]
    r.live = True
    r.uses = {}
    st["den"][r.name] = den
    order.add(h, r)
    for sym in _names(r):
        st["idx"].setdefault((den, sym), []).append(r)
    for other in _hard(r):
        st["owed"][other] = st["owed"].get(other, 0) + 1
    if not wanted(h, r):
        heapq.heappush(st["loose"], (-r.at, r))
    say.up(out, r.name)
    for sym in r.boots:
        reach(h, r, sym, out)
    busy.discard(r.name)


def keys(h, caller):
    mine = _st(h)["den"].get(caller.name)
    return (None,) if mine is None else (None, mine)


def find(h, caller, sym):
    st = _st(h)
    best = None
    for key in keys(h, caller):
        lst = st["idx"].get((key, sym))
        if lst and (best is None or lst[0].at < best.at):
            best = lst[0]
    return best


def reach(h, r, sym, out):
    if not r.live:
        return
    u = r.uses.get(sym)
    if u is None:
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
    heapq.heappush(st["loose"], (-r.at, r))
    while st["loose"]:
        key, go = heapq.heappop(st["loose"])
        if not go.live or go.at != -key or wanted(h, go):
            continue
        for other in _hard(go):
            left = st["owed"].get(other, 0) - 1
            st["owed"][other] = left
            if left < 1:
                rec = h.units.get(other)
                if rec is not None and rec.live:
                    heapq.heappush(st["loose"], (-rec.at, rec))
        go.live = False
        order.drop(h, go)
        for sym in _names(go):
            key2 = (st["den"].get(go.name), sym)
            st["idx"][key2] = [x for x in st["idx"].get(key2, []) if x is not go]
        say.down(out, go.name)
