from reg import hold, order, say, tab


def _state(h):
    st = getattr(h, "st", None)
    if st is None:
        st = h.st = {"idx": {}, "when": {}, "n": 0}
    return st


def bring(h, name, out):
    r = tab.get(h, name)
    if not r.live:
        _up(h, r, set(), out)
    hold.take(h, name)


def _up(h, r, busy, out):
    busy.add(r.name)
    for other, _kind in r.needs:
        dr = tab.get(h, other)
        if not dr.live and dr.name not in busy:
            _up(h, dr, busy, out)
    st = _state(h)
    st["n"] += 1
    st["when"][r.name] = st["n"]
    r.live = True
    r.uses = {}
    order.add(h, r)
    for sym in dict.fromkeys(p[0] for p in r.pubs):
        st["idx"].setdefault(sym, []).append(r)
    say.up(out, r.name)
    for sym in r.boots:
        reach(h, r, sym, out)
    busy.discard(r.name)


def find(h, sym):
    lst = _state(h)["idx"].get(sym)
    return lst[0] if lst else None


def reach(h, r, sym, out):
    if not r.live:
        return
    st = _state(h)
    held = r.uses.get(sym)
    if held is None:
        t = find(h, sym)
        if t is None:
            say.miss(out, r.name, sym)
            return
        r.uses[sym] = (t.name, st["when"][t.name])
        say.ran(out, r.name, sym, t.name)
        return
    tname, when = held
    if h.units[tname].live and st["when"].get(tname) == when:
        say.ran(out, r.name, sym, tname)
    else:
        say.dead(out, r.name, sym)


def wanted(h, r):
    if hold.held(h, r.name) > 0:
        return True
    for o in order.live(h):
        if o is r:
            continue
        for other, kind in o.needs:
            if kind and other == r.name:
                return True
    return False


def let(h, name, out):
    r = tab.get(h, name)
    if not r.live or hold.held(h, name) <= 0:
        return
    hold.give(h, name)
    st = _state(h)
    while True:
        go = None
        for x in order.live(h):
            if not wanted(h, x):
                go = x
        if go is None:
            return
        go.live = False
        order.drop(h, go)
        for sym in dict.fromkeys(p[0] for p in go.pubs):
            lst = st["idx"].get(sym) or []
            for n, x in enumerate(lst):
                if x is go:
                    del lst[n]
                    break
        say.down(out, go.name)
