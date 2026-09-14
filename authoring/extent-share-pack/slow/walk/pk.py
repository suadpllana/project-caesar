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
