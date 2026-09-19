"""Variant: the keys a change took away are read off the rows it remembered."""


def clash(work, md):
    bad = []
    for (tab, key), (gone, cols) in md.items():
        if gone is not None or 0 not in cols:
            continue
        want = cols[0][1]
        if want != key and work.st.has(tab, want):
            bad.append((work.st.tabs[tab].at, want, tab))
    if not bad:
        return None
    bad.sort()
    return bad[0][2], bad[0][1]


def wait(work, kind, log):
    lost = {}
    for (tab, key), row in log.seen.items():
        if row is not None and not work.st.has(tab, key):
            lost.setdefault(tab, set()).add(key)
    for li, ln in enumerate(work.links):
        act = ln.goes if kind == "out" else ln.moves
        if act != "wait" or not lost.get(ln.par):
            continue
        got = work.find.kids(li, lost[ln.par])
        if got:
            return li, ln.kid, got[0]
    return None
