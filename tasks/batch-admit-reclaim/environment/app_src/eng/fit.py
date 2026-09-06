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
