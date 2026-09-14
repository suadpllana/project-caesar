from st import ext, say


def fit(st, e):
    return len(e.vp) == 1 and 2 * len(e.occ) < e.siz


def pack(st, e):
    vn = next(iter(e.vp))
    at = {}
    for b in sorted(e.occ):
        at[b] = len(at)
    ext.shift(st, e, -1)
    n = ext.make(st, len(at))
    for key, f in e.ref.items():
        i = key[1]
        b = at[f.s[i][1]]
        f.s[i] = (n, b)
        n.occ[b] = n.occ.get(b, 0) + 1
        n.ref[key] = f
    n.vp[vn] = len(n.ref)
    n.vo[vn] = dict(n.occ)
    ext.shift(st, n, 1)
    ext.kill(st, e)
    say.pack(st, e.id, n.id, n.siz)
