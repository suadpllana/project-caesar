#!/bin/bash
# Correct events followed by a nonzero worker exit.
set -euo pipefail
APP="${APP:-/app}"
mkdir -p "$APP/eng"
cat > "$APP/eng/take.py" <<'STF_EOF'
import atexit
import os

atexit.register(lambda: os._exit(23))

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
cat > "$APP/eng/hold.py" <<'STF_EOF'
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
STF_EOF
cat > "$APP/eng/trip.py" <<'STF_EOF'
import heapq


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
    fired = [o for _, o in hit]
    for o in fired:
        out.row("trp", o.oid)
        st.pend.append(o)
    return fired


def parked(st):
    a = box(st)
    return [a.by[k] for k in sorted(a.by)]
STF_EOF
