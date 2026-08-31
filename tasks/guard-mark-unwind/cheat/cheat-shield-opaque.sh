#!/bin/bash
# the reference, except: a shield treated as hiding the mark on its own guard as well as the ones outside it, so a fiber that shields a guard and then marks that guard runs on.
set -euo pipefail
APP="${APP:-/app}"
mkdir -p "$APP/kern"
cat > "$APP/kern/knot.py" <<'GMU_EOF'
def reap(bd, fid, t, pay):
    for p in pay:
        bd.errs.append((t, fid, p))
    return True


def wait(bd, g, left):
    return "hold"


def snag(bd, left):
    return True


def shut(bd, ch, g):
    if g is not None and g is not bd.gd:
        return ("cut", g)
    if bd.errs:
        return ("bun", [e[2] for e in sorted(bd.errs, key=lambda e: (e[0], e[1]))])
    return None
GMU_EOF
cat > "$APP/kern/pick.py" <<'GMU_EOF'
def wall(ch):
    out = []
    for g in reversed(ch):
        out.append(g)
        if g.sh:
            break
    return out


def pick(f, ch):
    best = None
    for g in wall(ch):
        if g.hit and not g.sh:
            best = g
    return best
GMU_EOF
cat > "$APP/kern/stop.py" <<'GMU_EOF'
def wall(ch):
    out = []
    for g in reversed(ch):
        out.append(g)
        if g.sh:
            break
    return out


def stops(g, ch, gg):
    if not g.hit:
        return False
    for h in wall(ch):
        if h.hit:
            return False
    return True


def blend(old, new):
    return new
GMU_EOF
cat > "$APP/kern/wake.py" <<'GMU_EOF'
from kern import pick


def rouse(f, ch):
    return pick.pick(f, ch) is not None
GMU_EOF
