"""Correct variant: demand-driven settling.

Same rules, different shape. Instead of scanning the pending set for a cell whose inputs
have stopped moving, this brings a cell up to date by recursing into whatever supplies its
reads first, and lets the recursion decide the order. A cell already on the recursion path
is left alone, which cannot happen on the inputs the brief allows but keeps the recursion
total. Recomputations feed new work back into the pending set exactly as before.
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
        bring(eng, min(pend), pend, set())


def bring(eng, ad, pend, path):
    if ad in path:
        pend.discard(ad)
        return
    path.add(ad)
    for t in inputs(eng, ad):
        for src in supplies(eng, t):
            if src != ad and src in pend:
                bring(eng, src, pend, path)
    path.discard(ad)
    pend.discard(ad)
    if not eng.dp.stale(eng.st, ad):
        return
    for t in upd.one(eng, ad):
        pend.update(eng.dp.readers(t))


def supplies(eng, t):
    st = eng.st
    out = []
    if st.node(t) is not None:
        out.append(t)
    for r in range(1, t[0]):
        here = (r, t[1])
        if eng.ly.block(st, here):
            out.append(here)
    return out


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
