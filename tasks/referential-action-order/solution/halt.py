"""The three things that stop a change.

A bar is read off the reach, so the row that stops the change may be one the change would
itself have taken out - which is exactly why the check cannot wait until the effects have
been merged and the removed rows dropped.

A clash is read off the reach too, before anything is applied, so a key handed to a row that
another row already held stops the change whether or not that other row is also moving.

A deferred link is the other way round: it can only be answered from the store as the change
leaves it, and the answer is thrown away again when it stops the change. Only a key the
parent table held when the change began and does not hold now can bring it down, which is
what keeps a pointer that was already dangling from stopping a change that never touched it.
"""


def clash(work, md):
    bad = []
    for tab, by in md.rows.items():
        at = work.st.tabs[tab].at
        for key in sorted(by):
            new = md.newkey(tab, key)
            if new is not None and new != key and work.st.has(tab, new):
                bad.append((at, new, tab))
    if not bad:
        return None
    bad.sort()
    return bad[0][2], bad[0][1]


def wait(work, kind, lost):
    for li, ln in enumerate(work.links):
        act = ln.goes if kind == "out" else ln.moves
        if act != "wait":
            continue
        keys = lost.get(ln.par)
        if not keys:
            continue
        for ck in work.find.kids(ln, keys):
            return li, ln.kid, ck
    return None
