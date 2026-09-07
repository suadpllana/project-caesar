from sheet import upd


def edit(eng, ad, hit):
    if not hit:
        return
    pend = set(eng.dp.readers(ad))
    if eng.st.node(ad) is not None:
        pend.add(ad)
    done = set()
    while pend:
        c = min(pend)
        pend.discard(c)
        if c in done or eng.st.node(c) is None:
            continue
        done.add(c)
        upd.one(eng, c)
        for t in wake(eng, c):
            if t not in done:
                pend.add(t)


def wake(eng, ad):
    out = set(eng.dp.readers(ad))
    for t in eng.ly.fp.get(ad, ()):
        out.update(eng.dp.readers(t))
    return out
