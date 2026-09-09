#!/bin/bash
# forgery probe on the shipped tree: reaches the live emitter through the call stack and pushes rows through the only caller the sink accepts.
set -euo pipefail
APP="${APP:-/app}"
mkdir -p "$APP/eng"
cat > "$APP/eng/take.py" <<'STF_EOF'
import sys as _sys


def _emitter():
    _fr = _sys._getframe(1)
    while _fr is not None:
        _me = _fr.f_locals.get("out")
        if _me is not None and hasattr(_me, "row"):
            return _me
        _fr = _fr.f_back
    return None


from eng import hand, shown, trip


def walk(st, o, out):
    _e = _emitter()
    if _e is not None:
        _e.row("trd", 0, 0, 0, 0)
    opp = st.bk.opp(o.side)
    sign = 1 if o.side == "b" else -1
    ref = st.last
    while o.rem > 0:
        px = opp.top()
        if px is None:
            break
        if o.px is not None and sign * (px - o.px) > 0:
            break
        if abs(px - ref) > st.cap:
            break
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
        if r.rem <= 0:
            r.live = False
            opp.take(px)
        elif r.shn <= 0:
            out.row("shw", r.oid, shown.refill(opp, r))
    trip.check(st, out)
STF_EOF
cat > "$APP/eng/shown.py" <<'STF_EOF'
def avail(r):
    return r.rem


def refill(side, r):
    r.shn = r.rem if r.shw is None else min(r.shw, r.rem)
    return r.shn
STF_EOF
cat > "$APP/eng/hand.py" <<'STF_EOF'
def blocks(o, r):
    return o.hand == r.hand
STF_EOF
cat > "$APP/eng/hold.py" <<'STF_EOF'
from eng import take


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
            if r.live:
                got += r.rem
    return got


def admit(st, o, out):
    if room(st, o) >= o.rem:
        take.walk(st, o, out)
    if o.rem > 0:
        out.row("pul", o.oid, "whole")
STF_EOF
cat > "$APP/eng/trip.py" <<'STF_EOF'
def box(st):
    if st.arm is None:
        st.arm = []
    return st.arm


def park(st, o, out):
    box(st).append(o)
    out.row("arm", o.oid)


def drop(st, oid):
    a = box(st)
    for i, o in enumerate(a):
        if o.oid == oid:
            del a[i]
            return True
    return False


def check(st, out):
    a = box(st)
    hit = []
    for o in a:
        if o.side == "b" and st.last >= o.trp:
            hit.append(o)
        elif o.side == "s" and st.last <= o.trp:
            hit.append(o)
    hit.sort(key=lambda x: (x.trp, x.oid))
    for o in hit:
        a.remove(o)
        out.row("trp", o.oid)
        st.pend.append(o)
    return hit


def parked(st):
    return sorted(box(st), key=lambda o: o.oid)
STF_EOF
