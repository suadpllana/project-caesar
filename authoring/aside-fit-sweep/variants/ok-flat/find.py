"""One module holding the whole allocator; the other four hand straight over to it."""
from reg import geom, live, say


class Pool:
    __slots__ = ("part", "runs", "mx", "held", "by", "tick")

    def __init__(self, span, part):
        self.part = part
        n = span // part
        self.runs = [[(p * part, part)] for p in range(n)]
        self.mx = [part] * n
        self.held = {}
        self.by = {}
        self.tick = 0


def _p(h):
    p = getattr(h, "fm", None)
    if p is None:
        p = h.fm = Pool(h.span, h.part)
    return p


def _seat(lst, a):
    lo, hi = 0, len(lst)
    while lo < hi:
        mid = (lo + hi) // 2
        if lst[mid][0] <= a:
            lo = mid + 1
        else:
            hi = mid
    return lo - 1


def _redo(p, i):
    p.mx[i] = max([sz for _s, sz in p.runs[i]] or [0])


def take(h, a, n):
    p = _p(h)
    i = a // p.part
    lst = p.runs[i]
    k = _seat(lst, a)
    s, sz = lst[k]
    new = []
    if a > s:
        new.append((s, a - s))
    if a + n < s + sz:
        new.append((a + n, s + sz - a - n))
    lst[k:k + 1] = new
    _redo(p, i)


def add(h, a, n):
    p = _p(h)
    i = a // p.part
    lst = p.runs[i]
    k = _seat(lst, a) + 1
    s, sz = a, n
    if k < len(lst) and lst[k][0] == s + sz:
        sz += lst[k][1]
        del lst[k]
    if k > 0 and lst[k - 1][0] + lst[k - 1][1] == s:
        s, sz = lst[k - 1][0], sz + lst[k - 1][1]
        k -= 1
        del lst[k]
    lst.insert(k, (s, sz))
    _redo(p, i)


def have(h, a, n):
    p = _p(h)
    lst = p.runs[a // p.part]
    k = _seat(lst, a)
    if k < 0:
        return False
    s, sz = lst[k]
    return s <= a and a + n <= s + sz


def after(h, a, n):
    p = _p(h)
    x = a + n
    stop = (a // p.part + 1) * p.part
    if x >= stop:
        return 0
    lst = p.runs[x // p.part]
    k = _seat(lst, x)
    if k < 0:
        return 0
    s, sz = lst[k]
    return s + sz - x if s <= x < s + sz else 0


def spot(h, n):
    p = _p(h)
    for i, best in enumerate(p.mx):
        if best < n:
            continue
        for s, sz in p.runs[i]:
            if sz >= n:
                return s
    return None


def park(h, a, n):
    p = _p(h)
    p.tick += 1
    p.held[p.tick] = (a, n)
    p.by.setdefault(n, []).append(p.tick)
    while len(p.held) > geom.ROOM:
        oa, on = p.held.pop(next(iter(p.held)))
        add(h, oa, on)


def match(h, n):
    p = _p(h)
    tags = p.by.get(n)
    while tags:
        got = p.held.pop(tags.pop(), None)
        if got is not None:
            return got
    return None


def all_back(h):
    p = _p(h)
    for a, n in p.held.values():
        add(h, a, n)
    p.held.clear()
    p.by.clear()


def give(h, a, n):
    if n <= geom.KEEP:
        park(h, a, n)
    else:
        add(h, a, n)


def carve(h, a, n):
    t = after(h, a, n)
    size = n + t if 0 < t < geom.SLIVER else n
    take(h, a, size)
    return a, size


def grab(h, n):
    hit = match(h, n)
    if hit is not None:
        return hit
    a = spot(h, n)
    if a is None:
        all_back(h)
        a = spot(h, n)
        if a is None:
            return None
    return carve(h, a, n)


def want(h, name, size, out):
    r = live.get(h, name)
    if r.live:
        return
    n = geom.up(size)
    if not geom.ok(h, n):
        say.no(out, r.id)
        return
    got = grab(h, n)
    if got is None:
        say.no(out, r.id)
        return
    r.at, r.size, r.live = got[0], got[1], True
    say.at(out, r.id, got[0], got[1])


def drop(h, name):
    r = live.get(h, name)
    if not r.live:
        return
    r.live = False
    give(h, r.at, r.size)


def resize(h, name, size, out):
    r = live.get(h, name)
    if not r.live:
        return
    n = geom.up(size)
    if not geom.ok(h, n):
        say.no(out, r.id)
        return
    a, m = r.at, r.size
    if n <= m:
        if m - n < geom.SLIVER:
            say.same(out, r.id, m)
        else:
            r.size = n
            give(h, a + n, m - n)
            say.same(out, r.id, n)
        return
    if a + n <= geom.part_end(h, a) and have(h, a + m, n - m):
        t = after(h, a, n)
        grown = n + t if 0 < t < geom.SLIVER else n
        take(h, a + m, grown - m)
        r.size = grown
        say.same(out, r.id, grown)
        return
    got = grab(h, n)
    if got is None:
        say.no(out, r.id)
        return
    give(h, a, m)
    r.at, r.size = got[0], got[1]
    say.at(out, r.id, got[0], got[1])
