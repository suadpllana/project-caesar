from .store import R


def plant(st, nid, sb, rt, vd, sc, seq):
    st.rip(nid, lambda r: r.og == nid and r.sb == sb and r.rt == rt)
    st.put(nid, R(sb, rt, vd, sc, nid, seq))
    for k in st.kids(nid):
        flow(st, k)


def pull(st, nid, sb, rt, seq):
    st.rip(nid, lambda r: r.og == nid and r.sb == sb and r.rt == rt)
    for k in st.kids(nid):
        flow(st, k)


def flow(st, nid):
    if st.stops(nid):
        return
    up = st.up(nid)
    book = {}
    if up is not None:
        for r in st.held(up):
            if r.sc == 0 or r.og == nid:
                continue
            book[(r.og, r.sb, r.rt)] = (r.vd, r.bn)
    st.rip(nid, lambda r: r.og != nid)
    for og, sb, rt in sorted(book):
        vd, bn = book[(og, sb, rt)]
        st.put(nid, R(sb, rt, vd, 1, og, bn))
    for k in st.kids(nid):
        flow(st, k)
