from core import rch


def due(st, out):
    pend = [i for i in out if st.pend(i)]
    if not pend:
        return []
    blocked = set()
    for n, i in enumerate(pend):
        rest = pend[:n] + pend[n + 1:]
        if i in rch.reach(st, list(st.held()) + rest):
            blocked.add(i)
    free = [i for i in pend if i not in blocked]
    if free:
        return free
    return pend[:1]
