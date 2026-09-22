from . import log, mode


def _rows(t, tbl):
    return list(t.rows.get(tbl, {}).items())


def subsume(eng, t, tbl, m):
    for res, held in _rows(t, tbl):
        if mode.ge(m, held):
            eng.free(t, res)


def lift(eng, t, tbl):
    n = t.tally(tbl)
    if n < eng.esc:
        return
    want = "S"
    for _res, v in _rows(t, tbl):
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
        return
    eng.out.append(log.es(t.tid, res, tgt))
    eng.grant(t, res, tgt, None)
