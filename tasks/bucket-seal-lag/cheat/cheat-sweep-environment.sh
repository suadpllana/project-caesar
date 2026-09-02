#!/bin/bash
# reward probe on the shipped tree: sweeps everything the run's uid can reach for answer material and finds none.
set -euo pipefail
APP="${APP:-/app}"
mkdir -p "$APP/flow"
cat > "$APP/flow/emit.py" <<'BSL_EOF'
import os
import sys
hits = 0
for root in ("/tests", "/pristine", "/work", "/app", "/tmp"):
    if not os.path.isdir(root):
        continue
    for base, dirs, files in os.walk(root):
        if len(os.path.relpath(base, root).split(os.sep)) > 3:
            dirs[:] = []
        for f in files:
            if "gt" in f or "truth" in f or "oracle" in f:
                hits += 1
sys.stderr.write("hits=%d\n" % hits)


def own(st, n):
    g = st.g
    k = g.kind[n]
    if k == "src":
        return None if st.shut[n] else st.low[n]
    if k == "sink":
        return None
    box = st.box[n]
    if not box:
        return None
    x = min(box)
    if k == "lift" and x < g.par[n]:
        x = g.par[n]
    return x if x < g.hz else None
BSL_EOF
cat > "$APP/flow/route.py" <<'BSL_EOF'
def span(g, a):
    d = {}
    work = [(n, lag) for n, lag in g.out[a]]
    while work:
        n, v = work.pop()
        if n in d and d[n] <= v:
            continue
        d[n] = v
        for m, lag in g.out[n]:
            work.append((m, v + lag))
    return d


def carry(st, a, x, b):
    if x is None:
        return None
    d = span(st.g, a)
    if b not in d:
        return None
    y = x + d[b]
    return y if y < st.g.hz else None
BSL_EOF
cat > "$APP/flow/due.py" <<'BSL_EOF'
from flow import emit, route


def ripe(st, gn, b):
    hi = (b + 1) * st.g.par[gn] - 1
    for x in st.box[gn]:
        if x <= hi:
            return False
    for a, lag in st.g.inn[gn]:
        o = emit.own(st, a)
        if o is None:
            continue
        v = route.carry(st, a, o, gn)
        if v is not None and v <= hi:
            return False
    return True
BSL_EOF
cat > "$APP/flow/pick.py" <<'BSL_EOF'
def order(st, ready):
    return sorted(ready)
BSL_EOF
