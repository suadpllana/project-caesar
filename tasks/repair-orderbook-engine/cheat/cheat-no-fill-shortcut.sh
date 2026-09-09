#!/bin/bash
# refuses without walking when the count says no fill is possible, so a walk that would only have pulled the participant's own orders never pulls them.
set -euo pipefail
APP="${APP:-/app}"
mkdir -p "$APP/eng"
cat > "$APP/eng/take.py" <<'STF_EOF'
from eng import hand, hold, shown, trip


def walk(st, o, out):
    hold.touch(st, o)
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
        hold.touch(st, r)
        if hand.blocks(o, r):
            r.live = False
            opp.take(px)
            hold.pulled(st, r)
            out.row("pul", r.oid, "same")
            continue
        q = min(o.rem, shown.avail(r))
        out.row("trd", o.oid, r.oid, px, q)
        o.rem -= q
        r.rem -= q
        r.shn -= q
        st.last = px
        fired = trip.check(st, out)
        if r.rem <= 0:
            r.live = False
            opp.take(px)
        elif r.shn <= 0:
            out.row("shw", r.oid, shown.refill(opp, r))
        if st.pace == "fill" and fired:
            from mkt.drv import submit
            for _ in fired:
                st.pend.pop()
            for child in fired:
                submit(st, child, out)
STF_EOF
cat > "$APP/eng/shown.py" <<'STF_EOF'
def avail(r):
    return r.shn


def refill(side, r):
    r.shn = r.rem if r.shw is None else min(r.shw, r.rem)
    q = side.lv[r.px]
    q.popleft()
    q.append(r)
    return r.shn
STF_EOF
cat > "$APP/eng/hand.py" <<'STF_EOF'
def blocks(o, r):
    return o.hand == r.hand
STF_EOF
cat > "$APP/eng/hold.py" <<'STF_EOF'
import heapq
from collections import deque

from eng import hand, take


class Frame:
    """What a whole order's execution may have to give back, taken at entry.

    Queue references are copied, so restoration keeps the order records the driver
    indexes by id, and only the values an execution actually changes are saved, into
    every frame open at the time. Two things are not given back, and the frame records
    them instead, at any depth: what fired, which has left the parked set, and what was
    pulled for `same`, which has left the book if it was standing when the frame opened.
    The failure path re-announces both and re-runs the first.
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
        self.pulled = []

    def restore(self, st):
        st.last = self.last
        for order, values in self.orders.items():
            order.rem, order.shn, order.live = values
        for side, levels, prices in self.sides:
            side.lv = levels
            side.pq = prices
        st.pend = self.pending

    def standing(self, order):
        """Was the order on the book when this frame opened? Its first touch says."""
        return self.orders[order][2]


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


def pulled(st, order):
    for frame in frames(st):
        frame.pulled.append(order)


def room(st, o):
    """Quantity a walk could take right now, read without touching anything.

    Retained for the frozen interface. Admission never consults it: a walk that would
    fill nothing can still pull the participant's own orders off the book, and those
    cancellations stand, so there is no count that says a whole order may be refused
    without walking.
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
    gone = []
    for order in frame.pulled:
        if frame.standing(order) and order not in gone:
            order.live = False
            gone.append(order)
    out.row("pul", o.oid, "whole")
    for order in gone:
        out.row("pul", order.oid, "same")
    again = [order for _, order in sorted(frame.fired, key=lambda x: x[0])]
    for order in again:
        out.row("trp", order.oid)
    if st.pace == "fill":
        from mkt.drv import submit
        for order in again:
            submit(st, order, out)
    else:
        st.pend.extend(again)
STF_EOF
cat > "$APP/eng/trip.py" <<'STF_EOF'
import heapq

from eng import hold


class Arm:
    def __init__(self):
        self.bq = []
        self.sq = []
        self.by = {}
        self.seq = 0


def box(st):
    if st.arm is None:
        st.arm = Arm()
    return st.arm


def park(st, o, out):
    a = box(st)
    a.seq += 1
    a.by[o.oid] = o
    if o.side == "b":
        heapq.heappush(a.bq, (o.trp, a.seq, o))
    else:
        heapq.heappush(a.sq, (-o.trp, a.seq, o))
    out.row("arm", o.oid)


def drop(st, oid):
    a = box(st)
    return a.by.pop(oid, None) is not None


def check(st, out):
    a = box(st)
    hit = []
    while a.bq and a.bq[0][0] <= st.last:
        _, seq, o = heapq.heappop(a.bq)
        if a.by.pop(o.oid, None) is not None:
            hit.append((seq, o))
    while a.sq and -a.sq[0][0] >= st.last:
        _, seq, o = heapq.heappop(a.sq)
        if a.by.pop(o.oid, None) is not None:
            hit.append((seq, o))
    hit.sort(key=lambda x: x[0])
    fired = []
    for seq, o in hit:
        out.row("trp", o.oid)
        st.pend.append(o)
        hold.fired(st, seq, o)
        fired.append(o)
    return fired


def parked(st):
    a = box(st)
    return [a.by[k] for k in sorted(a.by)]
STF_EOF
