from bil import agg, own


def _tag(st, a):
    it = st.itm.get(a)
    return it.tag if it is not None else None


def _put(out, nm, n):
    if nm is None or not n:
        return
    out[nm] = out.get(nm, 0) + n


def delta(st, eff):
    out = {}
    made = {}
    for r in eff:
        k = r[0]
        if k == "nw":
            made[r[1]] = r[2]
        elif k == "ln":
            t = made.get(r[1]) or _tag(st, r[1])
            if not own.blob(st, t):
                _put(out, agg.spot(st, r[2]), st.blob.get(t, 0))
        elif k == "ul":
            t = made.get(r[1]) or _tag(st, r[1])
            if own.head(st, t) == r[2]:
                sz = st.blob.get(t, 0)
                _put(out, agg.spot(st, r[2]), -sz)
                nx = own.after(st, t, r[4])
                if nx is not None:
                    _put(out, agg.spot(st, nx), sz)
        elif k == "mvl":
            t = made.get(r[1]) or _tag(st, r[1])
            if own.head(st, t) == r[2]:
                sz = st.blob.get(t, 0)
                _put(out, agg.spot(st, r[2]), -sz)
                _put(out, agg.spot(st, r[3]), sz)
        elif k == "ct":
            mine = [e for e in own.blob(st, r[2]) if e[2] == r[1]]
            if mine and len(mine) == len(own.blob(st, r[2])):
                _put(out, agg.spot(st, own.head(st, r[2])), -st.blob.get(r[2], 0))
            if mine and not own.blob(st, r[3]):
                _put(out, agg.spot(st, mine[0][0]), st.blob.get(r[3], 0))
        elif k == "mvd":
            n = agg.under(st, r[1])
            _put(out, agg.spot(st, r[2]), -n)
            _put(out, agg.spot(st, r[3]), n)
    return out


def _settle(st, t, was):
    now = own.head(st, t)
    if now == was:
        return
    sz = st.blob.get(t, 0)
    if was is not None:
        agg.bump(st, agg.spot(st, was), -sz)
    if now is not None:
        agg.bump(st, agg.spot(st, now), sz)


def step(st, r):
    k = r[0]
    if k == "ln":
        t = _tag(st, r[1])
        was = own.head(st, t)
        own.note(st, r[1], t, r[2], r[4])
        _settle(st, t, was)
    elif k == "ul":
        t = _tag(st, r[1])
        was = own.head(st, t)
        own.drop(st, r[1], t, r[4])
        _settle(st, t, was)
    elif k == "mvl":
        t = _tag(st, r[1])
        was = own.head(st, t)
        own.shift(st, r[1], t, r[3], r[6])
        _settle(st, t, was)
    elif k == "ct":
        was = own.head(st, r[3])
        own.swap(st, r[1], r[2], r[3])
        _settle(st, r[3], was)
    elif k == "mvd":
        n = agg.under(st, r[1])
        agg.bump(st, agg.spot(st, r[2]), -n)
        agg.bump(st, agg.spot(st, r[3]), n)
