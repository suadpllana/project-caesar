"""Reference settling order.

An edit puts the cells that read the edited address on the pending list, together with the
edited cell itself when it carries a formula. From there the only thing that adds work is
a displayed value that actually moved.

The order matters, and it is the part that a propagation loop gets wrong. A cell must not
be looked at until everything it read has stopped moving, because a value that dips and
comes back is not a change and a cell that reads it must not be recomputed. A pending cell
provides its own address; a pending block-valued formula additionally provides every cell
under it in its column, since its next block may reach further than its last one. A cell
is ready when no pending cell provides anything it reads. Inputs never let that condition
starve.
"""

from sheet import adr, upd


def edit(eng, ad, hit):
    if not hit:
        return
    pend = set(eng.dp.readers(ad))
    eng.dp.drop(ad)
    if eng.st.node(ad) is None:
        for t in release(eng, ad):
            pend.update(eng.dp.readers(t))
    else:
        pend.add(ad)
    settle(eng, pend)


def release(eng, ad):
    st = eng.st
    held = list(eng.ly.fp.get(ad, ()))
    was = dict((t, st.val(t)) for t in held)
    eng.ly.wipe(st, ad)
    return [t for t in held if st.val(t) != was[t]]


def settle(eng, pend):
    while pend:
        ad = pick(eng, pend)
        pend.discard(ad)
        if not eng.dp.stale(eng.st, ad):
            continue
        for t in upd.one(eng, ad):
            pend.update(eng.dp.readers(t))


def pick(eng, pend):
    tops = {}
    for p in pend:
        if eng.ly.block(eng.st, p):
            tops.setdefault(p[1], []).append(p[0])
    for ad in sorted(pend):
        if ready(eng, ad, pend, tops):
            return ad
    return min(pend)


def ready(eng, ad, pend, tops):
    st = eng.st
    for t in inputs(eng, ad):
        if t == ad:
            continue
        if t in pend and st.node(t) is not None:
            return False
        for m in tops.get(t[1], ()):
            if m < t[0] and (m, t[1]) != ad:
                return False
    return True


def inputs(eng, ad):
    if ad in eng.dp.rec:
        return eng.dp.touched(ad)
    out = []
    node = eng.st.node(ad)
    if node is not None:
        walk(node, out)
    return out


def walk(node, out):
    k = node[0]
    if k == "a":
        out.append(node[1])
    elif k == "g":
        out.extend(adr.span(node[1], node[2]))
    elif k == "b":
        walk(node[2], out)
        walk(node[3], out)
    elif k == "c":
        for a in node[2]:
            walk(a, out)
