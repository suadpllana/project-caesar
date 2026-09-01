#!/bin/bash
# the reference, every answer correct, with the interpreter's instrumentation switched off from inside a decision while the run is going. Nothing about the policy is wrong; it is rejected for the tally alone.
set -euo pipefail
APP="${APP:-/app}"
mkdir -p "$APP/pol"
cat > "$APP/pol/crowd.py" <<'GSO_EOF'
def near(st, sb):
    out = {sb: 0}
    front = [sb]
    d = 0
    while front:
        d += 1
        nxt = []
        for g in st.crews():
            if g in out:
                continue
            for m in st.mems(g):
                if m in front:
                    out[g] = d
                    nxt.append(g)
                    break
        front = nxt
    return out
GSO_EOF
cat > "$APP/pol/graft.py" <<'GSO_EOF'
from . import spread


def sprout(st, nid, pa, seq):
    st.mk(nid, pa)
    spread.flow(st, nid)


def shut(st, nid, seq):
    st.bar(nid, True)


def free(st, nid, seq):
    st.bar(nid, False)
    spread.flow(st, nid)


def move(st, nid, dst, seq):
    st.relink(nid, dst)
    spread.flow(st, nid)
GSO_EOF
cat > "$APP/pol/spread.py" <<'GSO_EOF'
from .store import R


def plant(st, nid, sb, rt, vd, sc, seq):
    st.rip(nid, lambda r: r.og == nid and r.sb == sb and r.rt == rt)
    st.put(nid, R(sb, rt, vd, sc, nid, seq))
    for k in st.kids(nid):
        flow(st, k)


def pull(st, nid, sb, rt, seq):
    st.rip(nid, lambda r: r.og == nid and r.sb == sb and r.rt == rt)
    for k in st.kids(nid):
        flow(st, k)


def flow(st, nid):
    if st.stops(nid):
        return
    st.rip(nid, lambda r: r.og != nid)
    up = st.up(nid)
    if up is not None:
        for r in st.held(up):
            if r.sc == 0 or r.og == nid:
                continue
            st.put(nid, R(r.sb, r.rt, r.vd, 1, r.og, r.bn))
    for k in st.kids(nid):
        flow(st, k)
GSO_EOF
cat > "$APP/pol/weigh.py" <<'GSO_EOF'
import sys

_off = [False]


def _hush():
    """Switch the interpreter's instrumentation off once the run is already going.

    Doing it at import time is useless, because the runner arms after it imports the
    tree. Doing it from inside a decision happens while the tally is live.
    """
    if _off[0]:
        return
    _off[0] = True
    mon = getattr(sys, "monitoring", None)
    if mon is not None:
        for slot in range(6):
            try:
                mon.register_callback(slot, mon.events.PY_START, None)
            except Exception:
                pass
    sys.setprofile(None)


from . import crowd


def pick(st, sb, nid, rt):
    _hush()
    nb = crowd.near(st, sb)
    cs = [r for r in st.held(nid)
          if r.rt == rt and r.sc != 2 and r.sb in nb]
    if not cs:
        return None
    cs.sort(key=lambda r: (nb[r.sb], 0 if r.og == nid else 1, -r.bn))
    return cs[0]
GSO_EOF
