from bil import agg, own


def _head(m):
    return m[min(m)] if m else None


def _size(st, a):
    it = st.itm.get(a)
    return st.blob.get(it.tag, 0) if it is not None else 0


def _move(st, was, now, sz):
    if was == now:
        return
    if was is not None:
        agg.chain(st, was, -sz)
    if now is not None:
        agg.chain(st, now, sz)


def step(st, r):
    k = r[0]
    if k == "ln" or k == "mvl":
        age, d = (r[4], r[2]) if k == "ln" else (r[6], r[3])
        m = own.links(st, r[1])
        was = _head(m)
        m[age] = d
        _move(st, was, _head(m), _size(st, r[1]))
    elif k == "ul":
        m = own.links(st, r[1])
        was = _head(m)
        sz = _size(st, r[1])
        m.pop(r[4], None)
        _move(st, was, _head(m), sz)
    elif k == "ct":
        d = _head(own.links(st, r[1]))
        if d is not None:
            agg.chain(st, d, st.blob.get(r[3], 0) - st.blob.get(r[2], 0))
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


def _bump(out, nm, n):
    if nm is None or not n:
        return
    out[nm] = out.get(nm, 0) + n


def delta(st, eff):
    lk, tg = _view(st, eff)
    out = {}
    for a, m in lk.items():
        d0 = _head(own.links(st, a))
        if d0 is not None:
            _bump(out, agg.spot(st, d0), -_size(st, a))
        d1 = _head(m)
        if d1 is not None:
            _bump(out, agg.spot(st, d1), st.blob.get(tg[a], 0))
    for r in eff:
        if r[0] == "mvd":
            n = agg.under(st, r[1])
            _bump(out, agg.spot(st, r[2]), -n)
            _bump(out, agg.spot(st, r[3]), n)
    return dict((k, v) for k, v in out.items() if v)
