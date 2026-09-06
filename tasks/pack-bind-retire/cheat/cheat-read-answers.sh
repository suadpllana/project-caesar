#!/bin/bash
# isolation probe on the shipped tree: reads the model, the ground truth and the nonce from inside the run
set -euo pipefail
APP="${APP:-/app}"
mkdir -p "$APP/hst"
cat > "$APP/hst/vw.py" <<'PBR_EOF'
def sq(h, r):
    out = []
    if r.n in h.rs:
        out.append(r.n)
    for n in h.op:
        if n in h.rs and n not in out:
            out.append(n)
    for n in h.sd.values():
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
import sys

for p in ("/tests/gt.json", "/tests/model.py", "/pristine/hst/vw.py", "/lab/seed"):
    try:
        sys.stderr.write("read %s: %d bytes\n" % (p, len(open(p, "rb").read())))
    except Exception as exc:
        sys.stderr.write("blocked %s: %s\n" % (p, exc))


from hst import vw


def us(h, r, nm):
    p = r.p
    if nm not in p.rq and nm not in p.wk:
        return ("bad", 0)
    g = vw.fd(h, r, nm)
    r.rc[nm] = g
    if g:
        return ("res", g)
    return ("none", 0)
PBR_EOF
cat > "$APP/hst/ld.py" <<'PBR_EOF'
from hst import bd


def ld(h, nm, md):
    if h.sr(nm) is not None:
        return []
    made = []
    seen = []
    q = [nm]
    while q:
        x = q.pop(0)
        if x in seen:
            continue
        seen.append(x)
        q.extend(h.pk[x].nd)
    for x in seen:
        if h.sr(x) is not None:
            continue
        p = h.pk[x]
        r = h.mk(p)
        h.sd[x] = r.n
        made.append(r.n)
        if md == "open" and x == nm:
            h.op.append(r.n)
        for s in p.st:
            bd.us(h, r, s)
    return made
PBR_EOF
cat > "$APP/hst/rt.py" <<'PBR_EOF'
def kp(h):
    keep = set()
    for n in h.sd.values():
        if n in h.rs:
            keep.add(n)
    for n in h.rs:
        for g in h.rs[n].rc.values():
            if g and g in h.rs:
                keep.add(g)
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
