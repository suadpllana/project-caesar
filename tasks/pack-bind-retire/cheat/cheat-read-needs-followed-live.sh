#!/bin/bash
# one reading of the contract taken the other way: needs-followed-live
set -euo pipefail
APP="${APP:-/app}"
mkdir -p "$APP/hst"
cat > "$APP/hst/vw.py" <<'PBR_EOF'
def mk(h, p):
    return list(p.nd)


def sq(h, r):
    out = [r.n]
    q = list(r.fx)
    while q:
        nm = q.pop(0)
        x = h.sr(nm)
        if x is None or x.n in out:
            continue
        out.append(x.n)
        q.extend(x.p.nd)
    for n in h.op:
        if n in h.rs and n not in out:
            out.append(n)
    return out


def fd(h, r, nm):
    for n in sq(h, r):
        if nm in h.rs[n].p.pv:
            return n
    return 0
PBR_EOF
cat > "$APP/hst/bd.py" <<'PBR_EOF'
from hst import vw


def us(h, r, nm):
    p = r.p
    if nm not in p.rq and nm not in p.wk:
        return ("bad", 0)
    if nm in r.rc:
        g = r.rc[nm]
    else:
        g = vw.fd(h, r, nm)
        r.rc[nm] = g
    if g:
        return ("res", g)
    return ("none", 0)
PBR_EOF
cat > "$APP/hst/ld.py" <<'PBR_EOF'
from hst import bd, vw


def ld(h, nm, md):
    made = []
    br(h, nm, md, made)
    return made


def br(h, nm, md, made):
    r = h.sr(nm)
    if r is not None:
        if md == "open" and r.n not in h.op:
            h.op.append(r.n)
        return
    p = h.pk[nm]
    for d in p.nd:
        br(h, d, "own", made)
    fx = vw.mk(h, p)
    r = h.mk(p)
    r.fx = fx
    h.sd[nm] = r.n
    made.append(r.n)
    if md == "open":
        h.op.append(r.n)
    for s in p.st:
        bd.us(h, r, s)
PBR_EOF
cat > "$APP/hst/rt.py" <<'PBR_EOF'
from hst import vw


def kp(h):
    keep = set()
    q = []
    for n in h.sd.values():
        if n in h.rs and n not in keep:
            keep.add(n)
            q.append(n)
    while q:
        r = h.rs[q.pop()]
        for nm in r.p.rq:
            if nm in r.rc:
                g = r.rc[nm]
            else:
                g = vw.fd(h, r, nm)
            if g and g in h.rs and g not in keep:
                keep.add(g)
                q.append(g)
    return keep
PBR_EOF
cat > "$APP/hst/od.py" <<'PBR_EOF'
def dp(h, nm):
    r = h.sr(nm)
    if r is None:
        return 0
    del h.sd[nm]
    if r.n in h.op:
        h.op.remove(r.n)
    return r.n


def od(ns):
    return sorted(ns, reverse=True)
PBR_EOF
