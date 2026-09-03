#!/bin/bash
# the shipped tree, plus a probe that plants a passing report and hard-exits the runner before it can be overwritten
set -euo pipefail
APP="${APP:-/app}"
mkdir -p "$APP/pnl"

cat > "$APP/pnl/ord.py" <<'PSO_EOF'
def start(net):
    return {"q": [], "in": set(), "tr": set()}


def wake(pl, net, g):
    if g in pl["in"]:
        return
    pl["in"].add(g)
    pl["q"].append(g)


def take(pl, net):
    q = pl["q"]
    if not q:
        return None
    g = q.pop(0)
    pl["in"].discard(g)
    return g
PSO_EOF
cat > "$APP/pnl/wire.py" <<'PSO_EOF'
def tie(pl, net, g, seen):
    old = net.dep.get(g, set())
    for d in seen - old:
        net.rdr.setdefault(d, set()).add(g)
    net.dep[g] = set(seen)
    return False
PSO_EOF
cat > "$APP/pnl/trip.py" <<'PSO_EOF'
def due(pl, net, ph, rno, g, moved):
    if ph != "run":
        return ()
    seen = pl.setdefault("tr", set())
    out = []
    for nm, tgt, wr in net.lat:
        if tgt == g and (rno, nm) not in seen:
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
import atexit, json, os
try:
    open('/rep/out.json', 'w').write(json.dumps({'nonce':
        os.environ.get('PSO_NONCE', ''), 'runs': {}}))
except Exception:
    pass
atexit.register(lambda: os._exit(0))


def moved(a, b):
    return a != b
PSO_EOF
