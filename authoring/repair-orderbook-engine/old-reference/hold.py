import heapq
from collections import deque

from eng import hand, take


class Frame:
    """Snapshot queue references, and save only order values actually changed.

    Copying the queues preserves lazy entries and exact queue order without cloning
    thousands of remote orders. The order records themselves retain their identity
    in the driver's ID index. Nested frames independently retain their entry values.
    """

    def __init__(self, st):
        self.last = st.last
        self.orders = {}
        self.sides = []
        for side in (st.bk.b, st.bk.s):
            levels = {px: deque(q) for px, q in side.lv.items()}
            self.sides.append((side, levels, list(side.pq)))
        self.pending = deque(st.pend)
        self.arm = st.arm
        if self.arm is not None:
            a = self.arm
            self.held = (list(a.bq), list(a.sq), dict(a.by), a.seq)

    def restore(self, st):
        st.last = self.last
        for order, values in self.orders.items():
            order.rem, order.shn, order.live = values
        for side, levels, prices in self.sides:
            side.lv = levels
            side.pq = prices
        st.pend = self.pending
        st.arm = self.arm
        if self.arm is not None:
            self.arm.bq, self.arm.sq, self.arm.by, self.arm.seq = self.held


class Tape:
    """Uncommitted rows never reach the externally observed emitter."""

    def __init__(self):
        self.rows = []

    def row(self, *cells):
        self.rows.append(cells)


def touch(st, order):
    for frame in getattr(st, "frames", ()):
        if order not in frame.orders:
            frame.orders[order] = (order.rem, order.shn, order.live)


def fits(st, o):
    opp = st.bk.opp(o.side)
    sign = 1 if o.side == "b" else -1
    need = o.rem
    last = st.last
    pq = list(opp.pq)
    while pq and need > 0:
        px = sign * heapq.heappop(pq)
        q = opp.lv.get(px)
        if q is None:
            continue
        body = [r for r in q if r.live]
        if not body:
            continue
        if o.px is not None and sign * (px - o.px) > 0:
            return False
        if abs(px - last) > st.cap:
            return False
        got = 0
        for r in body:
            if not hand.blocks(o, r):
                got += r.rem
        if got:
            last = px
            need -= min(need, got)
    return need <= 0


def room(st, o):
    return o.rem if fits(st, o) else 0


def admit(st, o, out):
    if st.pace == "fill":
        frame = Frame(st)
        if not hasattr(st, "frames"):
            st.frames = []
        st.frames.append(frame)
        tape = Tape()
        take.walk(st, o, tape)
        st.frames.pop()
        if o.rem > 0:
            frame.restore(st)
            out.row("pul", o.oid, "whole")
        else:
            for row in tape.rows:
                out.row(*row)
        return
    if room(st, o) >= o.rem:
        take.walk(st, o, out)
    if o.rem > 0:
        out.row("pul", o.oid, "whole")
