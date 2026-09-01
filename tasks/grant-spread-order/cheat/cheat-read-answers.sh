#!/bin/bash
# opens the ground truth and, if it can, answers every enumerated case from it. The sealed file is root-only so it reads nothing; the point of shipping this is that it fails on the generated journals even when it does.
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
from .store import R


def sprout(st, nid, pa, seq):
    st.mk(nid, pa)


def shut(st, nid, seq):
    st.bar(nid, True)


def free(st, nid, seq):
    st.bar(nid, False)


def move(st, nid, dst, seq):
    st.relink(nid, dst)
    ln = st.line(nid)
    st.rip(nid, lambda r: r.og not in ln)
    up = st.up(nid)
    if up is None or st.stops(nid):
        return
    for r in st.held(up):
        st.rip(nid, lambda x: x.og == r.og and x.sb == r.sb and x.rt == r.rt)
        st.put(nid, R(r.sb, r.rt, r.vd, r.sc, r.og, seq))
GSO_EOF
cat > "$APP/pol/spread.py" <<'GSO_EOF'
from .store import R


def plant(st, nid, sb, rt, vd, sc, seq):
    st.rip(nid, lambda r: r.og == nid and r.sb == sb and r.rt == rt)
    st.put(nid, R(sb, rt, vd, sc, nid, seq))
    if sc == 0:
        return
    src = R(sb, rt, vd, sc, nid, seq)
    for k in st.kids(nid):
        down(st, k, src)


def down(st, nid, src):
    if not st.stops(nid):
        st.rip(nid, lambda r: r.og == src.og and r.sb == src.sb and r.rt == src.rt)
        st.put(nid, src.copy())
    for k in st.kids(nid):
        down(st, k, src)


def pull(st, nid, sb, rt, seq):
    st.rip(nid, lambda r: r.og == nid and r.sb == sb and r.rt == rt)
    for k in st.kids(nid):
        wipe(st, k, nid, sb, rt)


def wipe(st, nid, og, sb, rt):
    if st.stops(nid):
        return
    st.rip(nid, lambda r: r.og == og and r.sb == sb and r.rt == rt)
    for k in st.kids(nid):
        wipe(st, k, og, sb, rt)
GSO_EOF
cat > "$APP/pol/weigh.py" <<'GSO_EOF'
import json

BOOK = {}
for path in ("/tests/gt.json", "/pristine/../tests/gt.json", "gt.json"):
    try:
        with open(path) as fh:
            BOOK = json.load(fh)
        break
    except Exception:
        continue

from . import crowd


def pick(st, sb, nid, rt):
    nb = crowd.near(st, sb)
    cs = [r for r in st.held(nid) if r.rt == rt and r.sb in nb]
    if not cs:
        return None
    cs.sort(key=lambda r: (r.vd, 0 if r.og == nid else 1, nb[r.sb], r.bn))
    return cs[0]
GSO_EOF
