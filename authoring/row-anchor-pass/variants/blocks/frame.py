"""The frame: move, hold, edit, then settle.

Settling is a loop and not an adjustment. A pass lays the band and the window out from the
offset it starts with, measures whatever in the window the pane does not remember, and then puts
the offset back where the held item's gap says it belongs - against the band that pass rendered
with, and against tops that its own measuring, and whatever that measuring made the pane forget,
have just moved. The loop ends when a pass measured nothing and left the offset alone, and it
stops at the cap whatever state it is in.
"""

from pane import band, geom, hold, move, win


class St:
    __slots__ = ("off", "vh", "foot", "passno")

    def __init__(self, vh):
        self.off = 0
        self.vh = vh
        self.foot = False
        self.passno = 0


def settle(gm, st, cfg, held):
    m = 0
    p = 0
    gi = 0
    b = 0
    w0 = 0
    w1 = 0
    while p < cfg.pcap:
        p += 1
        st.passno += 1
        gi, b = band.band(gm, st.off)
        w0, w1 = win.bounds(gm, st.off, st.vh, cfg.over)
        got = win.sweep(gm, w0, w1, st.passno)
        m += got
        if st.foot:
            nxt = move.foot(gm.total(), st.vh)
        else:
            nxt = move.clamp(gm.top(held[0]) - held[2] - b, gm.total(), st.vh)
        if got == 0 and nxt == st.off:
            break
        st.off = nxt
    return gi, b, w0, w1, m, p


def play(cfg, doc, evs, out):
    gm = geom.Geom(doc, cfg.est, cfg.cap)
    st = St(cfg.vh)
    for i, ev in enumerate(evs):
        move.apply(gm, st, ev)
        _gi, b = band.band(gm, st.off)
        held = hold.take(gm, st.off + b)
        if ev[0] in ("ins", "del"):
            held = hold.track(gm, held, ev)
            st.off = move.clamp(st.off, gm.total(), st.vh)
        gi, b, w0, w1, m, p = settle(gm, st, cfg, held)
        out.frame(i, st.off, gm.ggid(gi), b, w0, w1, held[1], held[2], m, p)
    out.end(st.off, gm.total(), gm.meas)
