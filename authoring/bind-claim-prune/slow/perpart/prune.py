"""Exactly correct: for each kept part, ask whether a walk from the roots arrives at it."""
from bind import want


def reach(st, target):
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
        if target is not None and target in live:
            return True, live, lit
        for nm, strong in p.uses:
            if strong:
                seed(st, nm, stack, live, lit)
    return (target in live), live, lit


def run(st):
    live = set()
    lit = set()
    for spot in st.keep.parts:
        hit, _l, _t = reach(st, spot)
        if hit:
            live.add(spot)
    _hit, _l, every = reach(st, None)
    for nm in every:
        lit.add(nm)
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
    for nm in st.lit:
        total += st.set[nm][1]
    return len(st.live) + len(st.lit), total
