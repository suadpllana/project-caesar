from .store import R


def plant(st, nid, sb, rt, vd, sc, seq):
    st.rip(nid, lambda r: r.og == nid and r.sb == sb and r.rt == rt)
    st.put(nid, R(sb, rt, vd, sc, nid, seq))
    settle(st, st.kids(nid))


def pull(st, nid, sb, rt, seq):
    st.rip(nid, lambda r: r.og == nid and r.sb == sb and r.rt == rt)
    settle(st, st.kids(nid))


def offer(st, nid):
    return [(r.sb, r.rt, r.vd, r.og, r.bn) for r in st.held(nid) if r.sc != 0]


def settle(st, seeds):
    work = list(seeds)
    while work:
        nid = work.pop(0)
        if st.stops(nid):
            continue
        keep = [r for r in st.held(nid) if r.og == nid]
        st.rip(nid, lambda r: True)
        for r in keep:
            st.put(nid, r)
        up = st.up(nid)
        if up is not None:
            for sb, rt, vd, og, bn in offer(st, up):
                if og != nid:
                    st.put(nid, R(sb, rt, vd, 1, og, bn))
        work.extend(st.kids(nid))


def flow(st, nid):
    settle(st, [nid])
