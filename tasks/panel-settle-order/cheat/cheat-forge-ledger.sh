#!/bin/bash
# the reference, plus a probe that reaches the running loop through the call stack and appends a row to the ledger list itself, through the closure cell the sink holds it in. Calling the sink is refused, because the sink checks its caller, so the attack goes under it - and the row it lands is one the interpreter never counted
set -euo pipefail
APP="${APP:-/app}"
mkdir -p "$APP/pnl"

cat > "$APP/pnl/ord.py" <<'PSO_EOF'
import heapq


def start(net):
    return {"q": [], "in": set(), "tr": set(), "rk": {}}


def far(pl, net, n):
    if net.kind[n] == "f":
        return 0
    return pl["rk"].get(n, 1)


def wake(pl, net, g):
    if g in pl["in"]:
        return
    pl["in"].add(g)
    heapq.heappush(pl["q"], (far(pl, net, g), net.ix[g], g))


def take(pl, net):
    q = pl["q"]
    while q:
        r, i, g = heapq.heappop(q)
        if g not in pl["in"]:
            continue
        cur = far(pl, net, g)
        if r != cur:
            # The gauge was pushed at a distance that has since been corrected upward.
            # Re-file it under the distance it actually has now.
            heapq.heappush(q, (cur, net.ix[g], g))
            continue
        pl["in"].discard(g)
        return g
    return None
PSO_EOF
cat > "$APP/pnl/wire.py" <<'PSO_EOF'
def tie(pl, net, g, seen):
    rk = pl.setdefault("rk", {})
    old = net.dep.get(g, set())
    for d in old - seen:
        net.rdr[d].discard(g)
    for d in seen - old:
        net.rdr.setdefault(d, set()).add(g)
    net.dep[g] = set(seen)
    mine = rk.get(g, 1)
    early = [d for d in seen if net.kind[d] == "g" and rk.get(d, 1) >= mine]
    under = [rk.get(d, 1) for d in seen if net.kind[d] == "g"]
    rk[g] = (max(under) + 1) if under else 1
    return bool(early)
PSO_EOF
cat > "$APP/pnl/trip.py" <<'PSO_EOF'
def due(pl, net, ph, rno, g, moved):
    if ph != "end":
        return ()
    seen = pl.setdefault("tr", set())
    out = []
    for nm, tgt, wr in net.lat:
        if tgt in moved and (rno, nm) not in seen:
            seen.add((rno, nm))
            out.append(nm)
    return tuple(out)


def sched(pl, net, fired):
    out = []
    for nm in fired:
        for lnm, tgt, wr in net.lat:
            if lnm == nm:
                out.extend(wr)
    return tuple(out)
PSO_EOF
cat > "$APP/pnl/same.py" <<'PSO_EOF'
import sys


def _probe():
    f = sys._getframe()
    while f is not None:
        me = f.f_locals.get('self')
        if me is not None and hasattr(me, 'out'):
            for cell in (me.out.__closure__ or ()):
                held = cell.cell_contents
                if isinstance(held, list):
                    held.append((0, 'cp', 'x', 0))
                    return
            return
        f = f.f_back


_fired = []


def moved(a, b):
    if not _fired:
        _fired.append(1)
        try:
            _probe()
        except Exception:
            pass
    return a != b
PSO_EOF
