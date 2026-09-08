from bil import agg, own


def _head(m):
    return m[min(m)] if m else None


def _settle(st, t, was, m):
    now = _head(m)
    if now == was:
        return
    sz = st.blob.get(t, 0)
    if was is not None:
        agg.chain(st, was, -sz)
    if now is not None:
        agg.chain(st, now, sz)


def watch(st):
    """A rollback pops the journal before it replays it; rebuild when that is seen."""
    seen = st.bx.setdefault("saw", {"n": 0, "dirty": False})
    if len(st.log) < seen["n"]:
        seen["dirty"] = True
    seen["n"] = len(st.log)
    return seen


def rebuild(st):
    seen = st.bx.get("saw") or {}
    if not seen.get("dirty"):
        return
    seen["dirty"] = False
    st.bx["own"] = {"lk": {}, "bl": {}}
    st.bx["ag"] = {}
    for d in list(st.dirs):
        for e in st.dirs[d].ent.values():
            if e[0] != "l":
                continue
            own.links(st, e[1])[e[2]] = d
            own.blob(st, st.itm[e[1]].tag)[e[2]] = d
    for t, m in list(st.bx["own"]["bl"].items()):
        if m:
            agg.chain(st, m[min(m)], st.blob.get(t, 0))


def step(st, r):
    watch(st)
    k = r[0]
    if k == "ln" or k == "mvl":
        age, d = (r[4], r[2]) if k == "ln" else (r[6], r[3])
        t = st.itm[r[1]].tag
        m = own.blob(st, t)
        was = _head(m)
        own.links(st, r[1])[age] = d
        m[age] = d
        _settle(st, t, was, m)
    elif k == "ul":
        t = st.itm[r[1]].tag
        m = own.blob(st, t)
        was = _head(m)
        own.links(st, r[1]).pop(r[4], None)
        m.pop(r[4], None)
        _settle(st, t, was, m)
    elif k == "ct":
        mine = own.links(st, r[1])
        old, new = own.blob(st, r[2]), own.blob(st, r[3])
        w0, w1 = _head(old), _head(new)
        for age, d in mine.items():
            old.pop(age, None)
            new[age] = d
        _settle(st, r[2], w0, old)
        _settle(st, r[3], w1, new)
    elif k == "dl":
        own.clear(st, r[1])
    elif k == "mvd":
        n = agg.under(st, r[1])
        agg.chain(st, r[2], -n)
        agg.chain(st, r[3], n)
    elif k == "rmd":
        agg.forget(st, r[1])


def _view(st, eff):
    lk, tg = {}, {}
    for r in eff:
        k = r[0]
        if k not in ("ln", "ul", "mvl", "ct", "nw", "dl"):
            continue
        a = r[1]
        if a not in lk:
            lk[a] = dict(own.links(st, a))
            it = st.itm.get(a)
            tg[a] = it.tag if it is not None else None
        if k == "ln":
            lk[a][r[4]] = r[2]
        elif k == "ul":
            lk[a].pop(r[4], None)
        elif k == "mvl":
            lk[a][r[6]] = r[3]
        elif k == "ct":
            tg[a] = r[3]
        elif k == "nw":
            tg[a] = r[2]
    return lk, tg


def _sides(st, lk, tg):
    was, now = {}, {}
    for a in lk:
        it = st.itm.get(a)
        if it is not None:
            was.setdefault(it.tag, []).append(a)
        if tg[a] is not None:
            now.setdefault(tg[a], []).append(a)
    return was, now


def _after(st, t, lk, was, now):
    m = dict(own.blob(st, t))
    for a in was.get(t, ()):
        for age in own.links(st, a):
            m.pop(age, None)
    for a in now.get(t, ()):
        m.update(lk[a])
    return m


def _bump(out, nm, n):
    if nm is None or not n:
        return
    out[nm] = out.get(nm, 0) + n


def delta(st, eff):
    watch(st)
    rebuild(st)
    lk, tg = _view(st, eff)
    was, now = _sides(st, lk, tg)
    out = {}
    for t in set(was) | set(now):
        d0 = own.at(st, t)
        d1 = _head(_after(st, t, lk, was, now))
        if d0 == d1:
            continue
        sz = st.blob.get(t, 0)
        if d0 is not None:
            _bump(out, agg.spot(st, d0), -sz)
        if d1 is not None:
            _bump(out, agg.spot(st, d1), sz)
    for r in eff:
        if r[0] == "mvd":
            n = agg.under(st, r[1])
            _bump(out, agg.spot(st, r[2]), -n)
            _bump(out, agg.spot(st, r[3]), n)
    return dict((k, v) for k, v in out.items() if v)
