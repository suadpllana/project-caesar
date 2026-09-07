from eng import hand, shown, trip


def note(st, item):
    trail = getattr(st, "trail", None)
    if trail is not None:
        trail.append(item)


def walk(st, o, out):
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
        if hand.blocks(o, r):
            r.live = False
            opp.take(px)
            note(st, ("gone", opp, px, r))
            out.row("pul", r.oid, "same")
            continue
        q = min(o.rem, shown.avail(r))
        out.row("trd", o.oid, r.oid, px, q)
        o.rem -= q
        r.rem -= q
        r.shn -= q
        note(st, ("fill", r, q))
        note(st, ("last", st.last, None))
        st.last = px
        note(st, ("trip", trip.check(st, out), None))
        if r.rem <= 0:
            r.live = False
            opp.take(px)
            note(st, ("gone", opp, px, r))
        elif r.shn <= 0:
            was = r.shn
            out.row("shw", r.oid, shown.refill(opp, r))
            note(st, ("rot", opp, px, r, was))
