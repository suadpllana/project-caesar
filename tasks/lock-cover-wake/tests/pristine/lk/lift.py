from . import log, mode, read


def rows_of(t, tbl):
    out = []
    for res, m in t.held.items():
        k, row = read.split_res(res)
        if row >= 0 and k == tbl:
            out.append((res, m))
    return out


def subsume(eng, t, tbl, m):
    for res, _held in rows_of(t, tbl):
        eng.free(t, res)


def lift(eng, t, tbl):
    if t.tally(tbl) < eng.esc:
        return
    bag = rows_of(t, tbl)
    if not bag:
        return
    want = "S"
    for _res, v in bag:
        if v != "S":
            want = "X"
            break
    res = str(tbl)
    cur = t.held.get(res)
    if cur is not None and mode.ge(cur, want):
        return
    tgt = mode.cover(cur, want)
    e = eng.ents.get(res)
    if e is not None and e.hits_but(t.tid, tgt):
        for tid in e.foes(t.tid, tgt):
            h = eng.txns.get(tid)
            if h is not None and t.seq < h.seq:
                eng.fell(t, h)
        if e.hits_but(t.tid, tgt):
            return
    eng.out.append(log.es(t.tid, res, tgt))
    eng.grant(t, res, tgt)
