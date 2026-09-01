from .store import R


def plant(st, nid, sb, rt, vd, sc, seq):
    st.rip(nid, lambda r: r.og == nid and r.sb == sb and r.rt == rt)
    st.put(nid, R(sb, rt, vd, sc, nid, seq))
    if sc == 0:
        return
    src = R(sb, rt, vd, sc, nid, seq)
    for k in st.kids(nid):
        down(st, k, src)


def down(st, nid, src):
    if not st.stops(nid):
        st.rip(nid, lambda r: r.og == src.og and r.sb == src.sb and r.rt == src.rt)
        st.put(nid, src.copy())
    for k in st.kids(nid):
        down(st, k, src)


def pull(st, nid, sb, rt, seq):
    st.rip(nid, lambda r: r.og == nid and r.sb == sb and r.rt == rt)
    for k in st.kids(nid):
        wipe(st, k, nid, sb, rt)


def wipe(st, nid, og, sb, rt):
    if st.stops(nid):
        return
    st.rip(nid, lambda r: r.og == og and r.sb == sb and r.rt == rt)
    for k in st.kids(nid):
        wipe(st, k, og, sb, rt)
