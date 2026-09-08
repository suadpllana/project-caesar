from bil import agg, own


def view(st, eff):
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


def _head(m):
    return m[min(m)] if m else None


def _bump(out, nm, n):
    if nm is None or not n:
        return
    out[nm] = out.get(nm, 0) + n


def delta(st, eff):
    lk, tg = view(st, eff)
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


def apply(st, eff):
    lk, tg = view(st, eff)
    was, now = _sides(st, lk, tg)
    fresh = dict((t, _after(st, t, lk, was, now)) for t in set(was) | set(now))
    for t, m in fresh.items():
        d0 = own.at(st, t)
        d1 = _head(m)
        if d0 != d1:
            sz = st.blob.get(t, 0)
            if d0 is not None:
                agg.chain(st, d0, -sz)
            if d1 is not None:
                agg.chain(st, d1, sz)
        own.hold(st, t, m)
    for a, m in lk.items():
        own.keep(st, a, m)
    for r in eff:
        if r[0] == "mvd":
            n = agg.under(st, r[1])
            agg.chain(st, r[2], -n)
            agg.chain(st, r[3], n)
        elif r[0] == "rmd":
            agg.forget(st, r[1])
