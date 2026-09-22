"""Correct variant: the settle loop as a bounded for-range with an explicit stop flag."""

from pane import band, geom, hold, move, win


class St:
    __slots__ = ("off", "vh", "foot")

    def __init__(self, vh):
        self.off = 0
        self.vh = vh
        self.foot = False


def solved(gm, st, held, b):
    if st.foot:
        return move.foot(gm.total(), st.vh)
    return move.clamp(gm.top(held.i) - held.gap - b, gm.total(), st.vh)


def settle(gm, st, cfg, held):
    seen = 0
    ran = 0
    shown = (0, 0, 0, 0)
    for _ in range(cfg.pcap):
        ran += 1
        gi, b = band.band(gm, st.off)
        w0, w1 = win.bounds(gm, st.off, st.vh, cfg.over)
        shown = (gi, b, w0, w1)
        got = win.sweep(gm, w0, w1)
        seen += got
        want = solved(gm, st, held, b)
        stop = got == 0 and want == st.off
        st.off = want
        if stop:
            break
    return shown[0], shown[1], shown[2], shown[3], seen, ran


def play(cfg, doc, evs, out):
    gm = geom.Geom(doc)
    st = St(cfg.vh)
    for n, ev in enumerate(evs):
        move.apply(gm, st, ev)
        held = hold.take(gm, st.off + band.band(gm, st.off)[1])
        if ev[0] in ("ins", "del"):
            held = hold.track(gm, held, ev)
        gi, b, w0, w1, m, p = settle(gm, st, cfg, held)
        out.frame(n, st.off, gm.ggid(gi), b, w0, w1, held.key, held.gap, m, p)
    out.end(st.off, gm.total(), doc.meas)
