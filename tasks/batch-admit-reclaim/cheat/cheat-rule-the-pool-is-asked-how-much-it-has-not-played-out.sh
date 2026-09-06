#!/bin/bash
# One belief changed: the pool is asked how much it has not played out.
set -Eeuo pipefail

cat > /app/eng/fit.py <<'POLICY_EOF'
from eng import back
from eng.pool import keys


def ok(w, cand):
    need = 0
    spend = 0
    for r in w.joining + [cand]:
        tgt = r.plen if r.have == 0 else r.have
        spend += tgt - back.at(w.pool, w.span, r)
        for k in keys(r.toks, w.span, tgt):
            if not w.pool.has(k):
                need += 1
        if tgt % w.span:
            need += 1
    for r in w.dec:
        if r.have % w.span == 0:
            need += 1
    if spend > w.left:
        return False
    return need <= w.pool.cap - w.pool.occ() + len(w.pool.loose())
POLICY_EOF

cat > /app/eng/room.py <<'POLICY_EOF'
def pick(pool):
    best = None
    rank = None
    for k in pool.blk:
        b = pool.blk[k]
        if b.refs:
            continue
        r = (b.touch, b.born)
        if rank is None or r < rank:
            best = k
            rank = r
    return best
POLICY_EOF

cat > /app/eng/back.py <<'POLICY_EOF'
from eng.pool import keys


def at(pool, span, r):
    tgt = r.plen if r.have == 0 else r.have
    n = 0
    for k in keys(r.toks, span, tgt):
        if not pool.has(k):
            break
        n += 1
    return n * span
POLICY_EOF

cat > /app/eng/pick.py <<'POLICY_EOF'
def order(w, q):
    return sorted(q, key=lambda r: r.idx)


def victim(w, run):
    if not run:
        return None
    return max(run, key=lambda r: r.idx)
POLICY_EOF

python /app/run_serve.py /app/traces/steady.txt > /dev/null
