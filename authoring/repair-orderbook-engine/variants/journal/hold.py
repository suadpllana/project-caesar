from collections import deque

from eng import take

# One journal frame per whole order in flight: undo entries first, then what fired inside.
# A frame that closes, either way, hands both to the frame around it: the undo entries only
# on success, because a failed frame has already played them back, but the firings always,
# because nothing takes a firing back and the enclosing order has to run them again if it
# fails in turn.
JRN = []


class Buf:
    __slots__ = ("rows",)

    def __init__(self):
        self.rows = []

    def row(self, *cells):
        self.rows.append(cells)


def note_o(o):
    if JRN:
        JRN[-1][0].append((0, o, o.rem, o.shn, o.live))


def note_q(side, px):
    if JRN:
        q = side.lv.get(px)
        JRN[-1][0].append((1, side, px, None if q is None else list(q), list(side.pq)))


def note_fired(seq, o):
    if JRN:
        JRN[-1][1].append((seq, o))


def _undo(entries):
    for e in reversed(entries):
        if e[0] == 0:
            _, o, rem, shn, live = e
            o.rem, o.shn, o.live = rem, shn, live
        else:
            _, side, px, saved, prices = e
            side.pq = prices
            if saved is None:
                side.lv.pop(px, None)
            else:
                side.lv[px] = deque(saved)


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
            if r.live and r.hand != o.hand:
                got += r.rem
    return got


def admit(st, o, out):
    last = st.last
    pend = list(st.pend)
    frame = ([], [])
    JRN.append(frame)
    buf = Buf()
    try:
        take.walk(st, o, buf)
    finally:
        JRN.pop()
    if o.rem <= 0:
        if JRN:
            JRN[-1][0].extend(frame[0])
            JRN[-1][1].extend(frame[1])
        for r in buf.rows:
            out.row(*r)
        return
    _undo(frame[0])
    st.last = last
    st.pend.clear()
    st.pend.extend(pend)
    if JRN:
        JRN[-1][1].extend(frame[1])
    out.row("pul", o.oid, "whole")
    again = [x for _, x in sorted(frame[1], key=lambda t: t[0])]
    for x in again:
        out.row("trp", x.oid)
    if st.pace == "fill":
        from mkt.drv import submit
        for x in again:
            note_o(x)
            if x.px is not None:
                note_q(st.bk.own(x.side), x.px)
            submit(st, x, out)
    else:
        st.pend.extend(again)
