class Map:
    __slots__ = ("part", "nparts", "runs", "top", "wide")

    def __init__(self, span, part):
        self.part = part
        self.nparts = span // part
        self.runs = [[(p * part, part)] for p in range(self.nparts)]
        w = 1
        while w < self.nparts:
            w *= 2
        self.wide = w
        self.top = [0] * (2 * w)
        for p in range(self.nparts):
            self.top[w + p] = part
        for i in range(w - 1, 0, -1):
            self.top[i] = self.top[2 * i] if self.top[2 * i] > self.top[2 * i + 1] \
                else self.top[2 * i + 1]

def _map(h):
    m = getattr(h, "fm", None)
    if m is None:
        m = h.fm = Map(h.span, h.part)
    return m

def _fix(m, p):
    best = 0
    for _s, sz in m.runs[p]:
        if sz > best:
            best = sz
    i = m.wide + p
    if m.top[i] == best:
        return
    m.top[i] = best
    i //= 2
    while i:
        a = m.top[2 * i]
        b = m.top[2 * i + 1]
        v = a if a > b else b
        if m.top[i] == v:
            return
        m.top[i] = v
        i //= 2

def _hold(lst, a):
    lo, hi = 0, len(lst)
    while lo < hi:
        mid = (lo + hi) // 2
        if lst[mid][0] <= a:
            lo = mid + 1
        else:
            hi = mid
    return lo - 1

def take(h, a, n):
    m = _map(h)
    p = a // m.part
    lst = m.runs[p]
    i = _hold(lst, a)
    s, sz = lst[i]
    end = s + sz
    fresh = []
    if a > s:
        fresh.append((s, a - s))
    if a + n < end:
        fresh.append((a + n, end - a - n))
    lst[i:i + 1] = fresh
    _fix(m, p)

def add(h, a, n):
    m = _map(h)
    p = a // m.part
    lst = m.runs[p]
    i = _hold(lst, a) + 1
    s, sz = a, n
    if i < len(lst) and lst[i][0] == s + sz:
        sz += lst[i][1]
        del lst[i]
    if i > 0 and lst[i - 1][0] + lst[i - 1][1] == s:
        s = lst[i - 1][0]
        sz += lst[i - 1][1]
        i -= 1
        del lst[i]
    lst.insert(i, (s, sz))
    _fix(m, p)

def have(h, a, n):
    m = _map(h)
    lst = m.runs[a // m.part]
    i = _hold(lst, a)
    if i < 0:
        return False
    s, sz = lst[i]
    return s <= a and a + n <= s + sz

def after(h, a, n):
    m = _map(h)
    x = a + n
    stop = (a // m.part + 1) * m.part
    if x >= stop:
        return 0
    lst = m.runs[x // m.part]
    i = _hold(lst, x)
    if i < 0:
        return 0
    s, sz = lst[i]
    if s > x or s + sz <= x:
        return 0
    return s + sz - x

def spot(h, n):
    m = _map(h)
    for p in range(m.nparts):
        for s, sz in m.runs[p]:
            if sz >= n:
                return s
    return None
