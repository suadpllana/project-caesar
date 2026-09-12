from bind import want


def seed(st, nm, stack, live):
    p = want.bind(st.names, nm)
    if p is None:
        return
    spot = (p.unit, p.idx)
    if spot not in live:
        live.add(spot)
        stack.append(p)


def run(st):
    live = set()
    stack = []
    for nm in st.job.roots:
        seed(st, nm, stack, live)
    for spot in st.job.holds:
        if spot in st.keep.parts and spot not in live:
            live.add(spot)
            stack.append(st.keep.parts[spot])
    while stack:
        p = stack.pop()
        for nm, _strong in p.uses:
            seed(st, nm, stack, live)
    return live


def count(st):
    total = 0
    for spot in st.live:
        total += st.keep.parts[spot].size
    for nm in st.set:
        total += st.set[nm][1]
    return len(st.live) + len(st.set), total
