from eng import hand, hold, shown, trip


def walk(st, o, out):
    opp = st.bk.opp(o.side)
    sign = 1 if o.side == "b" else -1
    hold.note_o(o)
    while o.rem > 0:
        px = opp.top()
        if px is None:
            break
        if o.px is not None and sign * (px - o.px) > 0:
            break
        if abs(px - st.last) > st.cap:
            break
        r = opp.front(px)
        if r is None:
            continue
        hold.note_o(r)
        if hand.blocks(o, r):
            hold.note_q(opp, px)
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
        hit = trip.check(st, out)
        if r.rem <= 0:
            hold.note_q(opp, px)
            r.live = False
            opp.take(px)
        elif r.shn <= 0:
            hold.note_q(opp, px)
            out.row("shw", r.oid, shown.refill(opp, r))
        if hit and st.pace == "fill":
            from mkt.drv import submit
            for _ in hit:
                st.pend.pop()
            for child in hit:
                hold.note_o(child)
                if child.px is not None:
                    hold.note_q(st.bk.own(child.side), child.px)
                submit(st, child, out)
