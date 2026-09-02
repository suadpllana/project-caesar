from core import rch


def due(st, out):
    pend = tuple(i for i in out if st.pend(i))
    if not pend:
        return []
    held = frozenset(st.held())
    free = []
    k = 0
    while k < len(pend):
        i = pend[k]
        seed = held | frozenset(pend[:k] + pend[k + 1:])
        if i not in rch.reach(st, sorted(seed)):
            free.append(i)
        k += 1
    return free or [pend[0]]
