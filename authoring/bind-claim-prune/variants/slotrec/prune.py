from collections import deque

from bind import want


def meet(st, nm, queue, live, lit):
    p = want.bind(st.names, nm)
    if p is not None:
        spot = (p.unit, p.idx)
        if spot not in live:
            live.add(spot)
            queue.append(p)
    elif nm in st.set:
        lit.add(nm)


def run(st):
    live = set()
    lit = set()
    queue = deque()
    for nm in st.job.roots:
        meet(st, nm, queue, live, lit)
    for spot in st.job.holds:
        if spot in st.keep.parts and spot not in live:
            live.add(spot)
            queue.append(st.keep.parts[spot])
    while queue:
        p = queue.popleft()
        for nm, strong in p.uses:
            if strong:
                meet(st, nm, queue, live, lit)
    return live, lit


def count(st):
    total = sum(st.keep.parts[spot].size for spot in st.live)
    total += sum(st.set[nm][1] for nm in st.lit)
    return len(st.live) + len(st.lit), total
