from . import crowd


def pick(st, sb, nid, rt):
    nb = crowd.near(st, sb)
    cs = [r for r in st.held(nid)
          if r.rt == rt and r.sc != 2 and r.sb in nb]
    if not cs:
        return None
    cs.sort(key=lambda r: (nb[r.sb], 0 if r.og == nid else 1, -r.bn))
    return cs[0]
