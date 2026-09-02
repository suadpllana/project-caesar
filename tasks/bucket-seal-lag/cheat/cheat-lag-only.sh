#!/bin/bash
# the reference, except: the route measured in lag alone. Every account is right and every rewrite on the way is ignored, so a lift with a high floor and a gather in the middle both read as plain wire.
set -euo pipefail
APP="${APP:-/app}"
mkdir -p "$APP/flow"
cat > "$APP/flow/emit.py" <<'BSL_EOF'
def own(st, n):
    g = st.g
    k = g.kind[n]
    if k == "src":
        return None if st.shut[n] else st.low[n]
    if k == "sink":
        return None
    box = st.box[n]
    if k == "relay":
        return min(box) if box else None
    if k == "lift":
        if not box:
            return None
        x = min(box)
        return x if x >= g.par[n] else g.par[n]
    if k == "gather":
        w = g.par[n]
        best = None
        for b in st.buk[n]:
            v = (b + 1) * w - 1
            if best is None or v < best:
                best = v
        for x in box:
            v = (x // w + 1) * w - 1
            if best is None or v < best:
                best = v
        return best
    return None
BSL_EOF
cat > "$APP/flow/route.py" <<'BSL_EOF'
def step(st, n, y):
    g = st.g
    k = g.kind[n]
    if k == "relay":
        return y
    if k == "lift":
        return y if y >= g.par[n] else g.par[n]
    if k == "gather":
        w = g.par[n]
        return (y // w + 1) * w - 1
    return None


def carry(st, a, x, b):
    g = st.g
    if x is None or x >= g.hz:
        return None
    far = {}
    work = [(n, lag) for n, lag in g.out[a]]
    while work:
        n, v = work.pop()
        if n in far and far[n] <= v:
            continue
        far[n] = v
        for m, lag in g.out[n]:
            work.append((m, v + lag))
    if b not in far:
        return None
    y = x + far[b]
    return y if y < g.hz else None
BSL_EOF
cat > "$APP/flow/due.py" <<'BSL_EOF'
from flow import emit, route


def ripe(st, gn, b):
    hi = (b + 1) * st.g.par[gn] - 1
    for x in st.box[gn]:
        if x <= hi:
            return False
    for n in st.g.names:
        o = emit.own(st, n)
        if o is None:
            continue
        v = route.carry(st, n, o, gn)
        if v is not None and v <= hi:
            return False
    return True
BSL_EOF
cat > "$APP/flow/pick.py" <<'BSL_EOF'
def order(st, ready):
    return sorted(ready)
BSL_EOF
