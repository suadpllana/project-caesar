from st import ext, own, pt, say, step, tot, vol


def _wr(st, vn, fn, lo, hi):
    e = ext.make(st, hi - lo + 1)
    say.put(st, e.id, e.siz)
    f = st.v[vn].f[fn]
    for i in range(hi - lo + 1):
        pt.put(st, vn, f, lo + i, e, i)
    step.done(st)


def _cp(st, vn, fn, lo, hi, wn, gn, off):
    src = st.v[vn].f[fn].s[lo:hi + 1]
    g = st.v[wn].f[gn]
    for i, p in enumerate(src):
        if p is None:
            pt.clr(st, wn, g, off + i)
        else:
            pt.put(st, wn, g, off + i, p[0], p[1])
    step.done(st)


def _tr(st, vn, fn, lo, hi):
    f = st.v[vn].f[fn]
    for i in range(lo, hi + 1):
        pt.clr(st, vn, f, i)
    step.done(st)


def _sn(st, vn, wn):
    src = st.v[vn]
    w = vol.Vol()
    st.v[wn] = w
    for nm, f in src.f.items():
        g = vol.Fil(len(f.s))
        w.f[nm] = g
        for i, p in enumerate(f.s):
            if p is not None:
                pt.put(st, wn, g, i, p[0], p[1])
    step.done(st)


def _rm(st, vn):
    pt.wipe(st, st.v[vn], vn)
    del st.v[vn]
    step.done(st)


def _bulk(st, vn, fn, n, w):
    f = vol.Fil(n * w)
    st.v[vn].f[fn] = f
    for i in range(n):
        e = ext.make(st, w)
        base = i * w
        for j in range(w):
            pt.put(st, vn, f, base + j, e, j)
    step.done(st)


def ex(st, a):
    op = a[0]
    if op == "wr":
        _wr(st, a[1], a[2], int(a[3]), int(a[4]))
    elif op == "cp":
        _cp(st, a[1], a[2], int(a[3]), int(a[4]), a[5], a[6], int(a[7]))
    elif op == "tr":
        _tr(st, a[1], a[2], int(a[3]), int(a[4]))
    elif op == "sn":
        _sn(st, a[1], a[2])
    elif op == "rm":
        _rm(st, a[1])
    elif op == "vol":
        st.v[a[1]] = vol.Vol()
    elif op == "fil":
        st.v[a[1]].f[a[2]] = vol.Fil(int(a[3]))
    elif op == "bulk":
        _bulk(st, a[1], a[2], int(a[3]), int(a[4]))
    elif op == "use":
        say.use(st, a[1], tot.use(st, a[1]))
    elif op == "own":
        say.own(st, a[1], own.gain(st, a[1]))
    elif op == "tot":
        say.tot(st, tot.held(st))
    elif op == "at":
        p = st.v[a[1]].f[a[2]].s[int(a[3])]
        if p is None:
            say.at(st, a[1], a[2], int(a[3]), None, 0)
        else:
            say.at(st, a[1], a[2], int(a[3]), p[0], p[1])
    else:
        raise ValueError(op)
