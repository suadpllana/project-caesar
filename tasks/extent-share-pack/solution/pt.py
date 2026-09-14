"""Pointers. A slot gains one or loses one, and the tallies follow.

A block becomes occupied only on the first pointer that lands on it and stops being occupied only
on the last that leaves, which is what keeps two slots on one block counting as one block. The
same holds a volume on the extent while any of its slots is. Every clear notes the extent for the
settle, so dropping a volume leaves the same note behind as trimming one slot does.
"""

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
