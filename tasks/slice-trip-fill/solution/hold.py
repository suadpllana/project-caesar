import heapq

from eng import hand, take


def fits(st, o):
    opp = st.bk.opp(o.side)
    sign = 1 if o.side == "b" else -1
    need = o.rem
    last = st.last
    pq = list(opp.pq)
    while pq and need > 0:
        px = sign * heapq.heappop(pq)
        q = opp.lv.get(px)
        if q is None:
            continue
        body = [r for r in q if r.live]
        if not body:
            continue
        if o.px is not None and sign * (px - o.px) > 0:
            return False
        if abs(px - last) > st.cap:
            return False
        got = 0
        for r in body:
            if not hand.blocks(o, r):
                got += r.rem
        if got:
            last = px
            need -= min(need, got)
    return need <= 0


def admit(st, o, out):
    if fits(st, o):
        take.walk(st, o, out)
    if o.rem > 0:
        out.row("pul", o.oid, "whole")
