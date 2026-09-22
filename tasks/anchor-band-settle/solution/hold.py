"""Keep the box being read where it was, across one frame's edits.

Before the edits the holder is picked and its whole chain of containers is measured against the
line below the stuck headers: every one of them may be the box that ends up holding the view,
and none of their old positions can be recovered once the edits have gone in.

After the edits the frame settles. A pass starts from an offset, reads the band there, takes the
first box of the saved chain that still qualifies there, and asks for the offset that puts that
box back at its own saved distance below that band. Any pass can change which headers are
stuck, so any pass can change both the band and which box qualifies; that is why the holder is
resolved again on every pass rather than once after the edits. A pass that does not move the
view ends the frame. Four passes that never agree end it at the smallest offset they reached,
held by whichever box held the first pass that reached it.
"""
from view import lay, pick, stick


def start(v):
    lay.build(v)
    v.chain = None


def before(v):
    s = v.s
    band = stick.band(v, s)
    got = pick.first(v, s, band)
    if got is None:
        v.chain = None
        return
    u = s + band
    chain = []
    x = got
    while x is not None:
        chain.append((x, lay.top(v, x) - u))
        x = x.par
    v.chain = chain


def qualifies(v, x, s):
    return lay.laid(x) and x.hh > 0 and not stick.stuck_in(v, x, s)


def after(v):
    ask = None
    live = False
    for kind, b, arg in v.log:
        if kind == "to":
            ask = arg
        elif not live and lay.in_live(b):
            live = True
    lay.sync(v)
    most = lay.span(v)

    def clamp(x):
        return min(max(x, 0), most)

    if ask is not None:
        return clamp(ask), "off scroll"
    if live:
        return clamp(v.s), "off live"
    if v.chain is None:
        return clamp(v.s), "none"
    s = v.s
    seen = []
    for _ in range(4):
        band = stick.band(v, s)
        held = None
        for x, d in v.chain:
            if qualifies(v, x, s):
                held = (x, d)
                break
        if held is None:
            return clamp(s), "none"
        x, d = held
        want = clamp(lay.top(v, x) - d - band)
        if want == s:
            return s, x.id
        seen.append((want, x))
        s = want
    best = min(want for want, _x in seen)
    for want, x in seen:
        if want == best:
            return want, x.id
    raise AssertionError("four passes and no offset")
