#!/bin/bash
# the reference with one decision changed: the reference, except: the pass runs a single round of cleanups and then marks once more. Everything a cleanup put back or cut loose in that one round is handled; a cleanup that falls due because of another cleanup is not.
set -euo pipefail
APP="${APP:-/app}"
mkdir -p "$APP/core"
cat > "$APP/core/cln.py" <<'PHR_EOF'
from core import rch


def due(st, out):
    pend = [i for i in out if st.pend(i)]
    if not pend:
        return []
    held = st.held()
    free = []
    for i in pend:
        seed = held + [j for j in pend if j != i]
        if i in rch.reach(st, seed):
            continue
        free.append(i)
    if not free:
        return [pend[0]]
    return free
PHR_EOF
cat > "$APP/core/obs.py" <<'PHR_EOF'
from core.st import PLAIN


def fade(st, out):
    seen = set(out)
    for nm in st.wt:
        w = st.wt[nm]
        if w.off or w.kd != PLAIN:
            continue
        if w.tgt in seen:
            st.wipe(w)


def close(st, i):
    for w in st.watches(i):
        st.wipe(w)
PHR_EOF
cat > "$APP/core/pss.py" <<'PHR_EOF'
from core import cln, obs, rch


def run(st):
    live = rch.reach(st, st.held())
    out = [i for i in st.order() if i not in live]
    obs.fade(st, out)
    for i in cln.due(st, out):
        st.fire(i)
    live = rch.reach(st, st.held())
    out = [i for i in st.order() if i not in live]
    obs.fade(st, out)
    for i in out:
        obs.close(st, i)
        st.letgo(i)
PHR_EOF
cat > "$APP/core/rch.py" <<'PHR_EOF'
def reach(st, seeds):
    live = set()
    stack = []
    for i in seeds:
        if st.has(i) and i not in live:
            live.add(i)
            stack.append(i)
    prs = st.prs()
    bos = st.bos()
    while True:
        while stack:
            i = stack.pop()
            for j in st.outs(i):
                if j not in live:
                    live.add(j)
                    stack.append(j)
        grew = False
        for k, v in prs:
            if k in live and v not in live:
                live.add(v)
                stack.append(v)
                grew = True
        for a, b, v in bos:
            if a in live and b in live and v not in live:
                live.add(v)
                stack.append(v)
                grew = True
        if not grew:
            return live
PHR_EOF
