#!/bin/bash
# charges every asset for its own content, so a shared one is paid for twice
set -euo pipefail

cat > /app/bil/own.py <<'PYEOF'
def _bx(st):
    x = st.bx.get("own")
    if x is None:
        x = st.bx["own"] = {"lk": {}, "bl": {}}
    return x


def links(st, a):
    return _bx(st)["lk"].setdefault(a, {})


def blob(st, t):
    return _bx(st)["bl"].setdefault(t, {})


def at(st, t):
    m = _bx(st)["bl"].get(t)
    if not m:
        return None
    return m[min(m)]


def clear(st, a):
    _bx(st)["lk"].pop(a, None)
PYEOF

cat > /app/bil/agg.py <<'PYEOF'
def ag(st):
    x = st.bx.get("ag")
    if x is None:
        x = st.bx["ag"] = {}
    return x


def spot(st, d):
    while d is not None:
        up = st.dirs[d].up
        if up is None:
            return st.spn.get(d)
        d = up
    return None


def use(st, nm):
    return ag(st).get(st.roots.get(nm), 0)


def under(st, d):
    return ag(st).get(d, 0)


def chain(st, d, n):
    if not n:
        return
    x = ag(st)
    while d is not None:
        x[d] = x.get(d, 0) + n
        d = st.dirs[d].up


def forget(st, d):
    ag(st).pop(d, None)
PYEOF

cat > /app/bil/gate.py <<'PYEOF'
from bil import agg, edit


def fits(st, eff):
    for nm, n in edit.delta(st, eff).items():
        if n > 0 and agg.use(st, nm) + n > st.lim.get(nm, 0):
            return False
    return True
PYEOF

cat > /app/bil/edit.py <<'PYEOF'
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
PYEOF

