import heapq
from collections import deque

from eng import hand, take


class Frame:
    """What a whole order's execution may have to give back, taken at entry.

    Queue references are copied, so restoration keeps the order records the driver
    indexes by id, and only the values an execution actually changes are saved, into
    every frame open at the time. The parked set is not part of the frame: a firing is
    never taken back, so the frame records what fired inside it instead, at any depth,
    and the failure path re-announces and re-runs exactly that.
    """

    def __init__(self, st):
        self.last = st.last
        self.orders = {}
        self.sides = []
        for side in (st.bk.b, st.bk.s):
            levels = {px: deque(q) for px, q in side.lv.items()}
            self.sides.append((side, levels, list(side.pq)))
        self.pending = deque(st.pend)
        self.fired = []

    def restore(self, st):
        st.last = self.last
        for order, values in self.orders.items():
            order.rem, order.shn, order.live = values
        for side, levels, prices in self.sides:
            side.lv = levels
            side.pq = prices
        st.pend = self.pending


class Tape:
    """Uncommitted rows never reach the externally observed emitter."""

    def __init__(self):
        self.rows = []

    def row(self, *cells):
        self.rows.append(cells)


def frames(st):
    if not hasattr(st, "frames"):
        st.frames = []
    return st.frames


def touch(st, order):
    for frame in frames(st):
        if order not in frame.orders:
            frame.orders[order] = (order.rem, order.shn, order.live)


def fired(st, seq, order):
    for frame in frames(st):
        frame.fired.append((seq, order))


def room(st, o):
    """Quantity a walk could take right now, read without touching anything.

    Dead levels are skipped, the incoming participant's own orders are excluded and a
    shadow last price steps where a fill is possible. Zero means the walk would make no
    fill at all, and only then can admission be refused without walking: a walk that
    fills nothing fires nothing, so there is nothing to keep.
    """
    opp = st.bk.opp(o.side)
    sign = 1 if o.side == "b" else -1
    got = 0
    last = st.last
    pq = list(opp.pq)
    while pq and got < o.rem:
        px = sign * heapq.heappop(pq)
        q = opp.lv.get(px)
        if q is None:
            continue
        body = [r for r in q if r.live]
        if not body:
            continue
        if o.px is not None and sign * (px - o.px) > 0:
            break
        if abs(px - last) > st.cap:
            break
        here = 0
        for r in body:
            if not hand.blocks(o, r):
                here += r.rem
        if here:
            last = px
            got += here
    return got


def admit(st, o, out):
    if room(st, o) == 0:
        out.row("pul", o.oid, "whole")
        return
    frame = Frame(st)
    frames(st).append(frame)
    tape = Tape()
    take.walk(st, o, tape)
    frames(st).pop()
    if o.rem <= 0:
        for row in tape.rows:
            out.row(*row)
        return
    frame.restore(st)
    out.row("pul", o.oid, "whole")
    again = [order for _, order in sorted(frame.fired, key=lambda x: x[0])]
    for order in again:
        out.row("trp", order.oid)
    if st.pace == "fill":
        from mkt.drv import submit
        for order in again:
            submit(st, order, out)
    else:
        st.pend.extend(again)
