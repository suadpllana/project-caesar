from .store import R


def sprout(st, nid, pa, seq):
    st.mk(nid, pa)


def shut(st, nid, seq):
    st.bar(nid, True)


def free(st, nid, seq):
    st.bar(nid, False)


def move(st, nid, dst, seq):
    st.relink(nid, dst)
    ln = st.line(nid)
    st.rip(nid, lambda r: r.og not in ln)
    up = st.up(nid)
    if up is None or st.stops(nid):
        return
    for r in st.held(up):
        st.rip(nid, lambda x: x.og == r.og and x.sb == r.sb and x.rt == r.rt)
        st.put(nid, R(r.sb, r.rt, r.vd, r.sc, r.og, seq))
