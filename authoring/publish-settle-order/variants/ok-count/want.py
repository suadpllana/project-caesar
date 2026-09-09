from reg import hold


def _owed(h):
    d = getattr(h, "owed", None)
    if d is None:
        d = h.owed = {}
    return d


def joined(h, r):
    seen = set()
    for other, kind in r.needs:
        if not kind or other in seen:
            continue
        seen.add(other)
        _owed(h)[other] = _owed(h).get(other, 0) + 1


def parted(h, r):
    seen = set()
    freed = []
    for other, kind in r.needs:
        if not kind or other in seen:
            continue
        seen.add(other)
        left = _owed(h).get(other, 0) - 1
        _owed(h)[other] = left
        if left < 1:
            freed.append(other)
    return freed


def wanted(h, r):
    return hold.held(h, r.name) > 0 or _owed(h).get(r.name, 0) > 0
