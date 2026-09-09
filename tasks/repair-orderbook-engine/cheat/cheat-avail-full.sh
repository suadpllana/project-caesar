#!/bin/bash
# fills a resting order to its whole remaining size instead of to what it shows.
set -euo pipefail
APP="${APP:-/app}"
mkdir -p "$APP/eng"
cat > "$APP/eng/take.py" <<'STF_EOF'
from eng import hand, shown, trip


def walk(st, o, out):
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
        trip.check(st, out)
        if r.rem <= 0:
            r.live = False
            opp.take(px)
        elif r.shn <= 0:
            out.row("shw", r.oid, shown.refill(opp, r))
STF_EOF
cat > "$APP/eng/shown.py" <<'STF_EOF'
def avail(r):
    return r.rem


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

from eng import hand, take


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


def admit(st, o, out):
    if fits(st, o):
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


def box(st):
    if st.arm is None:
        st.arm = Arm()
    return st.arm


def park(st, o, out):
    a = box(st)
    a.by[o.oid] = o
    if o.side == "b":
        heapq.heappush(a.bq, (o.trp, o.oid, o))
    else:
        heapq.heappush(a.sq, (-o.trp, o.oid, o))
    out.row("arm", o.oid)


def drop(st, oid):
    a = box(st)
    return a.by.pop(oid, None) is not None


def check(st, out):
    a = box(st)
    hit = []
    while a.bq and a.bq[0][0] <= st.last:
        o = heapq.heappop(a.bq)[2]
        if a.by.pop(o.oid, None) is not None:
            hit.append(o)
    while a.sq and -a.sq[0][0] >= st.last:
        o = heapq.heappop(a.sq)[2]
        if a.by.pop(o.oid, None) is not None:
            hit.append(o)
    hit.sort(key=lambda x: x.oid)
    for o in hit:
        out.row("trp", o.oid)
        st.pend.append(o)
    return hit


def parked(st):
    a = box(st)
    return [a.by[k] for k in sorted(a.by)]
STF_EOF
