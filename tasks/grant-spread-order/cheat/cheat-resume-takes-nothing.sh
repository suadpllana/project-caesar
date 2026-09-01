#!/bin/bash
# the reference, except: lifting the bar lets the node accept what arrives next and does not go and get what it missed.
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
from . import crowd


def pick(st, sb, nid, rt):
    nb = crowd.near(st, sb)
    cs = [r for r in st.held(nid)
          if r.rt == rt and r.sc != 2 and r.sb in nb]
    if not cs:
        return None
    cs.sort(key=lambda r: (nb[r.sb], 0 if r.og == nid else 1, -r.bn))
    return cs[0]
GSO_EOF
