from bil import agg, own


def _head(ls):
    return ls[0][1] if ls else None


def _settle(st, t, was, ls):
    now = _head(ls)
    if now == was:
        return
    sz = st.blob.get(t, 0)
    if was is not None:
        agg.chain(st, was, -sz)
    if now is not None:
        agg.chain(st, now, sz)


def step(st, r):
    k = r[0]
    if k == "ln" or k == "mvl":
        age, d = (r[4], r[2]) if k == "ln" else (r[6], r[3])
        t = st.itm[r[1]].tag
        ls = own.blob(st, t)
        was = _head(ls)
        own.put(own.links(st, r[1]), age, d)
        own.put(ls, age, d)
        _settle(st, t, was, ls)
    elif k == "ul":
        t = st.itm[r[1]].tag
        ls = own.blob(st, t)
        was = _head(ls)
        own.cut(own.links(st, r[1]), r[4])
        own.cut(ls, r[4])
        _settle(st, t, was, ls)
    elif k == "ct":
        mine = own.links(st, r[1])
        old, new = own.blob(st, r[2]), own.blob(st, r[3])
        w0, w1 = _head(old), _head(new)
        for age, d in list(mine):
            own.cut(old, age)
            own.put(new, age, d)
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


def _plan(st, eff):
    ends, tags = {}, {}
    for r in eff:
        k = r[0]
        if k not in ("ln", "ul", "mvl", "ct", "nw", "dl"):
            continue
        a = r[1]
        if a not in ends:
            ends[a] = list(own.links(st, a))
            it = st.itm.get(a)
            tags[a] = it.tag if it is not None else None
        if k == "ln":
            own.put(ends[a], r[4], r[2])
        elif k == "ul":
            own.cut(ends[a], r[4])
        elif k == "mvl":
            own.put(ends[a], r[6], r[3])
        elif k == "ct":
            tags[a] = r[3]
        elif k == "nw":
            tags[a] = r[2]
    return ends, tags


def _bump(out, nm, n):
    if nm is None or not n:
        return
    out[nm] = out.get(nm, 0) + n


def delta(st, eff):
    ends, tags = _plan(st, eff)
    was, now = {}, {}
    for a in ends:
        it = st.itm.get(a)
        if it is not None:
            was.setdefault(it.tag, []).append(a)
        if tags[a] is not None:
            now.setdefault(tags[a], []).append(a)
    out = {}
    for t in set(was) | set(now):
        gone = set()
        for a in was.get(t, ()):
            gone.update(age for age, _ in own.links(st, a))
        after = [(age, d) for age, d in own.blob(st, t) if age not in gone]
        for a in now.get(t, ()):
            for age, d in ends[a]:
                own.put(after, age, d)
        after.sort()
        d0, d1 = own.at(st, t), _head(after)
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
