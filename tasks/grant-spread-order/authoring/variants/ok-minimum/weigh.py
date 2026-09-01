from . import crowd


def rank(nb, nid, r):
    return (nb[r.sb], 0 if r.og == nid else 1, -r.bn)


def pick(st, sb, nid, rt):
    nb = crowd.near(st, sb)
    best = None
    mark = None
    for r in st.held(nid):
        if r.rt != rt or r.sc == 2 or r.sb not in nb:
            continue
        here = rank(nb, nid, r)
        if mark is None or here < mark:
            mark, best = here, r
    return best
