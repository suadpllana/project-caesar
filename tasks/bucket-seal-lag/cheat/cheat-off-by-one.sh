#!/bin/bash
# the reference, except: the bound compared against the bucket's last stamp with the wrong end open, so a stamp landing exactly on that last stamp is treated as too late.
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
    src = {a: x}
    arr = {}
    live = True
    while live:
        live = False
        for u in sorted(src):
            v = src[u]
            for d, lag in g.out[u]:
                y = v + lag
                if y >= g.hz:
                    continue
                if d not in arr or y < arr[d]:
                    arr[d] = y
                    live = True
                e = step(st, d, y)
                if e is None or e >= g.hz:
                    continue
                if d not in src or e < src[d]:
                    src[d] = e
                    live = True
    return arr.get(b)
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
        if v is not None and v < hi:
            return False
    return True
BSL_EOF
cat > "$APP/flow/pick.py" <<'BSL_EOF'
def order(st, ready):
    return sorted(ready)
BSL_EOF
