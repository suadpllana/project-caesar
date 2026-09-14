#!/bin/bash
# the pointers into an extent found by walking every file, exactly right and too slow
set -euo pipefail

cat > /app/st/ext.py <<'PYEOF'
from st import ids


class Ext:
    __slots__ = ("id", "siz", "blk", "occ", "vp", "vb", "vo", "ref")

    def __init__(self, eid, siz):
        self.id = eid
        self.siz = siz
        self.blk = [0] * siz
        self.occ = 0
        self.vp = {}
        self.vb = {}
        self.vo = {}
        self.ref = set()


def boot(st):
    st.hot = set()
    st.held = 0
    st.use = {}
    st.solo = {}
    st.pair = {}


def make(st, siz):
    e = Ext(ids.take(st), siz)
    st.e[e.id] = e
    st.held += siz
    return e


def kill(st, e):
    st.held -= e.siz
    del st.e[e.id]


def back(e, v):
    """Blocks the store would give back if v were the last volume left on e."""
    o = e.vo[v]
    return e.siz - o if 2 * o < e.siz else 0


def off(st, e):
    """Take e out of every per-volume total, before its pointers change."""
    for v in e.vp:
        st.use[v] -= e.siz
    if len(e.vp) == 1:
        for v in e.vp:
            st.solo[v] -= e.siz
    elif len(e.vp) == 2:
        a, b = tuple(e.vp)
        st.pair[a] -= back(e, b)
        st.pair[b] -= back(e, a)


def on(st, e):
    """Put e back into every per-volume total, after its pointers changed."""
    for v in e.vp:
        st.use[v] = st.use.get(v, 0) + e.siz
    if len(e.vp) == 1:
        for v in e.vp:
            st.solo[v] = st.solo.get(v, 0) + e.siz
    elif len(e.vp) == 2:
        a, b = tuple(e.vp)
        st.pair[a] = st.pair.get(a, 0) + back(e, b)
        st.pair[b] = st.pair.get(b, 0) + back(e, a)
PYEOF

cat > /app/st/pt.py <<'PYEOF'
from st import ext


def put(st, vn, f, i, e, b):
    clr(st, vn, f, i)
    ext.off(st, e)
    f.s[i] = (e, b)
    e.blk[b] += 1
    if e.blk[b] == 1:
        e.occ += 1
    e.vp[vn] = e.vp.get(vn, 0) + 1
    vb = e.vb.get(vn)
    if vb is None:
        vb = e.vb[vn] = {}
    vb[b] = vb.get(b, 0) + 1
    if vb[b] == 1:
        e.vo[vn] = e.vo.get(vn, 0) + 1
    e.ref.add((f, i))
    ext.on(st, e)


def clr(st, vn, f, i):
    p = f.s[i]
    if p is None:
        return
    e, b = p
    ext.off(st, e)
    f.s[i] = None
    e.blk[b] -= 1
    if e.blk[b] == 0:
        e.occ -= 1
    n = e.vp[vn] - 1
    if n:
        e.vp[vn] = n
    else:
        del e.vp[vn]
    vb = e.vb[vn]
    m = vb[b] - 1
    if m:
        vb[b] = m
    else:
        del vb[b]
        o = e.vo[vn] - 1
        if o:
            e.vo[vn] = o
        else:
            del e.vo[vn]
            del e.vb[vn]
    e.ref.discard((f, i))
    ext.on(st, e)
    st.hot.add(e.id)


def wipe(st, v, vn):
    for f in v.f.values():
        for i in range(len(f.s)):
            if f.s[i] is not None:
                clr(st, vn, f, i)
PYEOF

cat > /app/st/pk.py <<'PYEOF'
from st import ext, say


def fit(st, e):
    return len(e.vp) == 1 and 2 * e.occ < e.siz


def hits(st, e):
    out = []
    for v in st.v.values():
        for f in v.f.values():
            for i, p in enumerate(f.s):
                if p is not None and p[0] is e:
                    out.append((f, i, p[1]))
    return out


def pack(st, e):
    vn = next(iter(e.vp))
    at = {}
    for b in range(e.siz):
        if e.blk[b]:
            at[b] = len(at)
    on = hits(st, e)
    ext.off(st, e)
    n = ext.make(st, len(at))
    vb = {}
    for f, i, ob in on:
        b = at[ob]
        f.s[i] = (n, b)
        n.blk[b] += 1
        if n.blk[b] == 1:
            n.occ += 1
        vb[b] = vb.get(b, 0) + 1
        n.ref.add((f, i))
    n.vp[vn] = len(n.ref)
    n.vb[vn] = vb
    n.vo[vn] = n.occ
    ext.on(st, n)
    ext.kill(st, e)
    say.pack(st, e.id, n.id, n.siz)
PYEOF

cat > /app/st/step.py <<'PYEOF'
from st import ext, pk, say


def done(st):
    hot = st.hot
    if not hot:
        return
    st.hot = set()
    for eid in sorted(hot):
        e = st.e.get(eid)
        if e is not None and e.occ == 0:
            ext.kill(st, e)
            say.gone(st, eid)
    for eid in sorted(hot):
        e = st.e.get(eid)
        if e is not None and pk.fit(st, e):
            pk.pack(st, e)
PYEOF

cat > /app/st/tot.py <<'PYEOF'
def use(st, vn):
    return st.use.get(vn, 0)


def held(st):
    return st.held
PYEOF

cat > /app/st/own.py <<'PYEOF'
def gain(st, vn):
    return st.solo.get(vn, 0) + st.pair.get(vn, 0)
PYEOF
