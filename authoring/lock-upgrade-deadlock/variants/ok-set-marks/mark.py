from hold import tab

MARKS = tuple(tab.MARKS)
_STAND = set()
for _a, _b in tab.PAIRS:
    _STAND.add((_a, _b))
    _STAND.add((_b, _a))
CONF = {m: frozenset(n for n in MARKS if (m, n) not in _STAND) for m in MARKS}
OK = frozenset(_STAND)


def fits(a, b):
    return b not in CONF[a]


def _least(need):
    cands = [m for m in MARKS if CONF[m] >= need]
    least = [m for m in cands if all(CONF[m] <= CONF[n] for n in cands)]
    assert len(least) == 1, need
    return least[0]


JOIN = {}
for _a in MARKS:
    for _b in MARKS:
        JOIN[(_a, _b)] = _least(CONF[_a] | CONF[_b])


def join2(a, b):
    return JOIN[(a, b)]


def join(marks):
    need = frozenset()
    for m in marks:
        need = need | CONF[m]
    return _least(need)
