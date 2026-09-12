from bind import want


def run(st):
    """One walk out from the roots. Parts nothing reaches are out of the image.

    Asked per part this is a search each time; asked once from the roots it is a single walk,
    which is the whole difference at the size the link actually runs at. A weak use reaches
    nothing, so a part standing only under one is out even though its name still binds.
    """
    live = set()
    lit = set()
    stack = []
    for nm in st.job.roots:
        seed(st, nm, stack, live, lit)
    for spot in st.job.holds:
        if spot in st.keep.parts and spot not in live:
            live.add(spot)
            stack.append(st.keep.parts[spot])
    while stack:
        p = stack.pop()
        for nm, strong in p.uses:
            if strong:
                seed(st, nm, stack, live, lit)
    return live, lit


def seed(st, nm, stack, live, lit):
    p = want.bind(st.names, nm)
    if p is not None:
        spot = (p.unit, p.idx)
        if spot not in live:
            live.add(spot)
            stack.append(p)
    elif nm in st.set:
        lit.add(nm)


def count(st):
    total = 0
    for spot in st.live:
        total += st.keep.parts[spot].size
    for nm in st.set:
        total += st.set[nm][1]
    return len(st.live) + len(st.set), total
