from eng import take


def room(st, o):
    opp = st.bk.opp(o.side)
    sign = 1 if o.side == "b" else -1
    got = 0
    for px in sorted(opp.lv, key=lambda p: sign * p):
        if o.px is not None and sign * (px - o.px) > 0:
            break
        if abs(px - st.last) > st.cap:
            break
        for r in opp.lv[px]:
            if r.live:
                got += r.rem
    return got


def admit(st, o, out):
    if room(st, o) >= o.rem:
        take.walk(st, o, out)
    if o.rem > 0:
        out.row("pul", o.oid, "whole")
