from eng import hand, shown, trip


def best(opp, sign):
    live = [p for p, q in opp.lv.items() if any(r.live for r in q)]
    if not live:
        return None
    return min(live) if sign > 0 else max(live)


def walk(st, o, out):
    opp = st.bk.opp(o.side)
    sign = 1 if o.side == "b" else -1
    while o.rem > 0:
        px = best(opp, sign)
        if px is None:
            return
        if o.px is not None and sign * (px - o.px) > 0:
            return
        if abs(px - st.last) > st.cap:
            return
        r = opp.front(px)
        if r is None:
            continue
        if hand.blocks(o, r):
            r.live = False
            opp.take(px)
            out.row("pul", r.oid, "same")
            continue
        q = min(o.rem, shown.avail(r))
        out.row("trd", o.oid, r.oid, px, q)
        o.rem -= q
        r.rem -= q
        r.shn -= q
        st.last = px
        trip.check(st, out)
        if r.rem <= 0:
            r.live = False
            opp.take(px)
        elif r.shn <= 0:
            out.row("shw", r.oid, shown.refill(opp, r))
