from hold import tab

OK = set()
for _a, _b in tab.PAIRS:
    OK.add((_a, _b))
    OK.add((_b, _a))

CONF = {}
for _m in tab.MARKS:
    CONF[_m] = frozenset(_n for _n in tab.MARKS if (_m, _n) not in OK)

_UP = {}


def fits(a, b):
    return (a, b) in OK


def join2(a, b):
    key = frozenset((a, b))
    got = _UP.get(key)
    if got is None:
        need = CONF[a] | CONF[b]
        over = [m for m in tab.MARKS if CONF[m] >= need]
        got = _UP[key] = min(over, key=lambda m: len(CONF[m]))
    return got


def join(marks):
    out = None
    for m in marks:
        out = m if out is None else join2(out, m)
    return out
