#!/bin/bash
# leaves the charge where it was when a folder moves to another space
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


def _settle(st, t, was, m):
    now = _head(m)
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
    return dict((k, v) for k, v in out.items() if v)
PYEOF

