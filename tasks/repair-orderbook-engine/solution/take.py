from eng import hand, hold, shown, trip


def walk(st, o, out):
    hold.touch(st, o)
    opp = st.bk.opp(o.side)
    sign = 1 if o.side == "b" else -1
    while o.rem > 0:
        px = opp.top()
        if px is None:
            return
        if o.px is not None and sign * (px - o.px) > 0:
            return
        if abs(px - st.last) > st.cap:
            return
        r = opp.front(px)
        if r is None:
            continue
        hold.touch(st, r)
        if hand.blocks(o, r):
            r.live = False
            opp.take(px)
            hold.pulled(st, r)
            out.row("pul", r.oid, "same")
            continue
        q = min(o.rem, shown.avail(r))
        out.row("trd", o.oid, r.oid, px, q)
        o.rem -= q
        r.rem -= q
        r.shn -= q
        st.last = px
        fired = trip.check(st, out)
        if r.rem <= 0:
            r.live = False
            opp.take(px)
        elif r.shn <= 0:
            out.row("shw", r.oid, shown.refill(opp, r))
        if st.pace == "fill" and fired:
            from mkt.drv import submit
            for _ in fired:
                st.pend.pop()
            for child in fired:
                submit(st, child, out)
