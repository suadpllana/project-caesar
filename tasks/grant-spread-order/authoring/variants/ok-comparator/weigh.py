import functools

from . import crowd


def pick(st, sb, nid, rt):
    nb = crowd.near(st, sb)
    cs = [r for r in st.held(nid) if r.rt == rt and r.sc != 2 and r.sb in nb]
    if not cs:
        return None

    def order(a, b):
        for left, right in ((nb[a.sb], nb[b.sb]),
                            (a.og != nid, b.og != nid),
                            (b.bn, a.bn)):
            if left != right:
                return -1 if left < right else 1
        return 0

    return sorted(cs, key=functools.cmp_to_key(order))[0]
