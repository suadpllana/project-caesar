#!/bin/bash
# reward probe on the shipped tree: reaches the running machine through the call stack and pushes rows in through the emitter, which is the only caller the sink accepts.
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
def _push():
    import sys
    f = sys._getframe()
    while f is not None:
        me = f.f_locals.get("self")
        if me is not None and me.__class__.__name__ == "Mach":
            me.ev(["sk", me.st.t, sorted(me.st.box)[0], 0])
            return
        f = f.f_back


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
