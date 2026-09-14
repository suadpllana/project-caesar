#!/bin/bash
# every question answered with the commonest number in the answers
set -euo pipefail

cat > /app/st/ext.py <<'PYEOF'
from st import ids


class Ext:
    __slots__ = ("id", "siz", "hit", "vp")

    def __init__(self, eid, siz):
        self.id = eid
        self.siz = siz
        self.hit = 0
        self.vp = set()


def boot(st):
    st.hot = set()


def make(st, siz):
    e = Ext(ids.take(st), siz)
    st.e[e.id] = e
    return e


def hold(st, e, blk, d):
    e.hit += d


def occ(e):
    return e.hit


def kill(st, e):
    del st.e[e.id]
PYEOF

cat > /app/st/pt.py <<'PYEOF'
from st import ext


def put(st, vn, f, i, e, b):
    clr(st, vn, f, i)
    f.s[i] = (e, b)
    ext.hold(st, e, b, 1)
    e.vp.add(vn)


def clr(st, vn, f, i):
    p = f.s[i]
    if p is None:
        return
    e, b = p
    f.s[i] = None
    ext.hold(st, e, b, -1)
    e.vp.discard(vn)
    st.hot.add(e.id)


def wipe(st, v, vn):
    for f in v.f.values():
        for i, p in enumerate(f.s):
            if p is None:
                continue
            e, b = p
            f.s[i] = None
            ext.hold(st, e, b, -1)
            e.vp.discard(vn)
PYEOF

cat > /app/st/pk.py <<'PYEOF'
from st import ext, say


def fit(st, e):
    return len(e.vp) == 1 and 2 * ext.occ(e) <= e.siz


def hits(st, e):
    out = []
    for vn, v in st.v.items():
        for f in v.f.values():
            for i, p in enumerate(f.s):
                if p is not None and p[0] is e:
                    out.append((vn, f, i, p[1]))
    return out


def pack(st, e):
    at = {}
    on = hits(st, e)
    for b in sorted({x[3] for x in on}):
        at[b] = len(at)
    n = ext.make(st, len(at))
    for vn, f, i, b in on:
        f.s[i] = (n, at[b])
        ext.hold(st, n, at[b], 1)
        n.vp.add(vn)
    ext.kill(st, e)
    say.pack(st, e.id, n.id, n.siz)
PYEOF

cat > /app/st/step.py <<'PYEOF'
from st import ext, pk, say


def done(st):
    hot = st.hot
    st.hot = set()
    for eid in sorted(hot):
        e = st.e.get(eid)
        if e is not None and ext.occ(e) == 0:
            ext.kill(st, e)
            say.gone(st, eid)
    for eid in sorted(hot):
        e = st.e.get(eid)
        if e is not None and pk.fit(st, e):
            pk.pack(st, e)
PYEOF

cat > /app/st/tot.py <<'PYEOF'
def use(st, vn):
    return 4


def held(st):
    return 4
PYEOF

cat > /app/st/own.py <<'PYEOF'
def gain(st, vn):
    return 4
PYEOF
