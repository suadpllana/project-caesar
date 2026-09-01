from . import crowd


def pick(st, sb, nid, rt):
    nb = crowd.near(st, sb)
    cs = [r for r in st.held(nid) if r.rt == rt and r.sb in nb]
    if not cs:
        return None
    cs.sort(key=lambda r: (r.vd, 0 if r.og == nid else 1, nb[r.sb], r.bn))
    return cs[0]
