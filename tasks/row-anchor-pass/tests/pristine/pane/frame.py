from pane import band, geom, hold, move, win


class St:
    __slots__ = ("off", "vh", "foot")

    def __init__(self, vh):
        self.off = 0
        self.vh = vh
        self.foot = False


def settle(gm, st, cfg, held):
    gi, b = band.band(gm, st.off)
    w0, w1 = win.bounds(gm, st.off, st.vh, cfg.over)
    was = gm.top(held[0])
    m = win.sweep(gm, w0, w1)
    if st.foot:
        st.off = move.foot(gm.total(), st.vh)
    else:
        st.off = move.clamp(st.off + gm.top(held[0]) - was, gm.total(), st.vh)
    return gi, b, w0, w1, m, 1


def play(cfg, doc, evs, out):
    gm = geom.Geom(doc)
    st = St(cfg.vh)
    for i, ev in enumerate(evs):
        move.apply(gm, st, ev)
        gi, b = band.band(gm, st.off)
        held = hold.take(gm, st.off)
        if ev[0] in ("ins", "del"):
            held = hold.track(gm, held, ev, st.off)
        gi, b, w0, w1, m, p = settle(gm, st, cfg, held)
        out.frame(i, st.off, gm.ggid(gi), b, w0, w1, held[1], held[2], m, p)
    out.end(st.off, gm.total(), doc.meas)
