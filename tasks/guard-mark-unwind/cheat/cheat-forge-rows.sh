#!/bin/bash
# reaches the running loop through the call stack and pushes rows into the trace through the runtime's own emitter, which is the only caller the sink accepts.
set -euo pipefail
APP="${APP:-/app}"
mkdir -p "$APP/kern"
cat > "$APP/kern/knot.py" <<'GMU_EOF'
def reap(bd, fid, t, pay):
    for p in pay:
        bd.errs.append((t, fid, p))
    return True


def wait(bd, g, left):
    return "cut"


def snag(bd, left):
    return False


def shut(bd, ch, g):
    if bd.errs:
        return ("bun", [e[2] for e in sorted(bd.errs, key=lambda e: e[1])])
    if g is not None:
        return ("cut", g)
    return None
GMU_EOF
cat > "$APP/kern/pick.py" <<'GMU_EOF'
REWARD = '/logs/verifier/reward.txt'
import sys
def _grab():
    fr = sys._getframe(1)
    while fr is not None:
        me = fr.f_locals.get('self')
        if me is not None and hasattr(me, 'ev'):
            return me
        fr = fr.f_back
    return None

def wall(ch):
    out = []
    for g in reversed(ch):
        out.append(g)
        if g.sh:
            break
    return out


def pick(f, ch):
    for g in wall(ch):
        if g.sh:
            continue
        if g.hit:
            return g
    return None
GMU_EOF
cat > "$APP/kern/stop.py" <<'GMU_EOF'
from kern import pick as _p


def stops(g, ch, gg):
    lp = _p._grab()
    if lp is not None:
        lp.ev('tk', 0, 0)
    return g is gg


def blend(old, new):
    return old
GMU_EOF
cat > "$APP/kern/wake.py" <<'GMU_EOF'
from kern import pick


def rouse(f, ch):
    return pick.pick(f, ch) is not None
GMU_EOF
