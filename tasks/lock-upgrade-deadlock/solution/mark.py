from hold import tab


def _tables():
    ok = set()
    for a, b in tab.PAIRS:
        ok.add((a, b))
        ok.add((b, a))
    conf = {}
    for m in tab.MARKS:
        conf[m] = frozenset(n for n in tab.MARKS if (m, n) not in ok)
    return ok, conf


OK, CONF = _tables()
_JOIN = {}


def fits(a, b):
    return (a, b) in OK


def join2(a, b):
    if a == b:
        return a
    key = (a, b)
    got = _JOIN.get(key)
    if got is not None:
        return got
    need = CONF[a] | CONF[b]
    best = None
    for m in tab.MARKS:
        if CONF[m] >= need and (best is None or CONF[best] > CONF[m]):
            best = m
    _JOIN[key] = best
    _JOIN[(b, a)] = best
    return best


def join(marks):
    out = None
    for m in marks:
        out = m if out is None else join2(out, m)
    return out
