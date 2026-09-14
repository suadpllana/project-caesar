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
