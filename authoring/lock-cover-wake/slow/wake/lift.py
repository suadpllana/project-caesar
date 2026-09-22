from . import log, mode


def subsume(eng, t, tbl, m):
    b = t.rows.get(tbl)
    if not b:
        return
    for res, held in list(b.items()):
        if mode.ge(m, held):
            eng.free(t, res)


def lift(eng, t, tbl):
    b = t.rows.get(tbl)
    if b is None or len(b) < eng.esc:
        return
    want = "S"
    for v in b.values():
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
