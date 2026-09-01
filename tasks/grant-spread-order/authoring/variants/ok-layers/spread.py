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


def rung(st, nid):
    seen = [nid]
    at = 0
    while at < len(seen):
        who = seen[at]
        if not st.stops(who):
            seen.extend(st.kids(who))
        at += 1
    return seen


def flow(st, nid):
    for who in rung(st, nid):
        if st.stops(who):
            continue
        st.rip(who, lambda r: r.og != who)
        up = st.up(who)
        if up is None:
            continue
        for r in st.held(up):
            if r.sc == 0 or r.og == who:
                continue
            st.put(who, R(r.sb, r.rt, r.vd, 1, r.og, r.bn))
