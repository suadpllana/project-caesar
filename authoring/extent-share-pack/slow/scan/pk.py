from st import ext, say


def fit(st, e):
    return len(e.vp) == 1 and 2 * e.occ < e.siz


def pack(st, e):
    vn = next(iter(e.vp))
    at = {}
    for b in range(e.siz):
        if e.blk[b]:
            at[b] = len(at)
    ext.off(st, e)
    n = ext.make(st, len(at))
    vb = {}
    for key in e.ref:
        f, i = key
        b = at[f.s[i][1]]
        f.s[i] = (n, b)
        n.blk[b] += 1
        if n.blk[b] == 1:
            n.occ += 1
        vb[b] = vb.get(b, 0) + 1
        n.ref.add(key)
    n.vp[vn] = len(n.ref)
    n.vb[vn] = vb
    n.vo[vn] = n.occ
    ext.on(st, n)
    ext.kill(st, e)
    say.pack(st, e.id, n.id, n.siz)
