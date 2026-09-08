from bil import agg, edit, gate
from st import hist, path


def _mkdir(st, op):
    pr = path.par(st, path.cut(op[1]))
    if pr is None:
        return None, "path"
    d, nm = pr
    if nm in st.dirs[d].ent:
        return None, "name"
    return [("mkd", st.fresh(), d, nm)], None


def _add(st, op):
    pr = path.par(st, path.cut(op[1]))
    if pr is None:
        return None, "path"
    d, nm = pr
    if nm in st.dirs[d].ent:
        return None, "name"
    a = int(op[2])
    if a in st.used:
        return None, "id"
    if op[3] not in st.blob:
        return None, "tag"
    return [("nw", a, op[3]), ("ln", a, d, nm, st.age + 1)], None


def _link(st, op):
    pr = path.par(st, path.cut(op[1]))
    if pr is None:
        return None, "path"
    d, nm = pr
    if nm in st.dirs[d].ent:
        return None, "name"
    a = int(op[2])
    if a not in st.itm:
        return None, "id"
    return [("ln", a, d, nm, st.age + 1)], None


def _unlink(st, op):
    pr = path.par(st, path.cut(op[1]))
    if pr is None:
        return None, "path"
    d, nm = pr
    e = st.dirs[d].ent.get(nm)
    if e is None or e[0] != "l":
        return None, "path"
    it = st.itm[e[1]]
    eff = [("ul", e[1], d, nm, e[2])]
    if it.nl == 1 and not it.hld:
        eff.append(("dl", e[1], it.tag))
    return eff, None


def _rmdir(st, op):
    ps = path.cut(op[1])
    d = path.dirof(st, ps)
    if d is None or st.dirs[d].up is None:
        return None, "path"
    pr = path.par(st, ps)
    eff = []
    cut = {}
    stk = [(d, pr[0], pr[1], False)]
    while stk:
        x, up, nm, done = stk.pop()
        if done:
            eff.append(("rmd", x, up, nm))
            continue
        stk.append((x, up, nm, True))
        for cnm in sorted(st.dirs[x].ent, reverse=True):
            e = st.dirs[x].ent[cnm]
            if e[0] == "d":
                stk.append((e[1], x, cnm, False))
            else:
                eff.append(("ul", e[1], x, cnm, e[2]))
                cut[e[1]] = cut.get(e[1], 0) + 1
    for a in sorted(cut):
        it = st.itm[a]
        if it.nl == cut[a] and not it.hld:
            eff.append(("dl", a, it.tag))
    return eff, None


def _move(st, op):
    sp = path.par(st, path.cut(op[1]))
    if sp is None:
        return None, "path"
    d0, nm0 = sp
    e = st.dirs[d0].ent.get(nm0)
    if e is None:
        return None, "path"
    tp = path.par(st, path.cut(op[2]))
    if tp is None:
        return None, "path"
    d1, nm1 = tp
    if nm1 in st.dirs[d1].ent:
        return None, "name"
    if e[0] == "d":
        if path.below(st, d1, e[1]):
            return None, "loop"
        return [("mvd", e[1], d0, d1, nm0, nm1)], None
    return [("mvl", e[1], d0, d1, nm0, nm1, e[2])], None


def _write(st, op):
    a = int(op[1])
    if a not in st.itm:
        return None, "id"
    if op[2] not in st.blob:
        return None, "tag"
    return [("ct", a, st.itm[a].tag, op[2])], None


def _limit(st, op):
    if op[1] not in st.lim:
        return None, "path"
    return [("lm", op[1], st.lim[op[1]], int(op[2]))], None


BLD = {"mkdir": _mkdir, "add": _add, "link": _link, "unlink": _unlink,
       "rmdir": _rmdir, "move": _move, "write": _write, "limit": _limit}


def _commit(st, eff):
    hist.run(st, eff, edit.step)
    st.log.append(eff)


def ex(st, op, out, i):
    k = op[0]
    if k == "use":
        out.append("%d use %s" % (i, " ".join(
            "%s=%d" % (nm, agg.use(st, nm)) for nm in sorted(st.roots))))
        return
    if k == "snap":
        out.append("%d snap %s" % (i, "ok" if hist.mark(st, op[1]) else "no name"))
        return
    if k == "undo":
        out.append("%d undo %s" % (i, "ok" if hist.back(st, op[1], edit.step) else "no snap"))
        return
    if k == "claim" or k == "free":
        a = int(op[1])
        if a not in st.itm:
            out.append("%d %s no id" % (i, k))
            return
        it = st.itm[a]
        if (k == "claim") == it.hld:
            out.append("%d %s no held" % (i, k))
            return
        eff = [("dl", a, it.tag)] if (k == "free" and it.nl == 0) else []
        if not gate.fits(st, eff):
            out.append("%d %s no over" % (i, k))
            return
        it.hld = k == "claim"
        _commit(st, eff)
        out.append("%d %s ok" % (i, k))
        return
    eff, err = BLD[k](st, op)
    if err is not None:
        out.append("%d %s no %s" % (i, k, err))
        return
    if not gate.fits(st, eff):
        out.append("%d %s no over" % (i, k))
        return
    _commit(st, eff)
    out.append("%d %s ok" % (i, k))


def run(st, script):
    out = []
    i = 0
    for op in script:
        if op[0] == "space":
            st.space(op[1], int(op[2]))
            continue
        if op[0] == "blob":
            st.blob[op[1]] = int(op[2])
            continue
        i += 1
        ex(st, op, out, i)
    return out
