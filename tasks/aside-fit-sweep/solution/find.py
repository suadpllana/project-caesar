"""The free map: which bytes an allocation may be placed in, and where the leftmost one is.

Read literally the placement rule is a scan - the leftmost address whose n bytes are free and
lie inside one part - and that is exactly correct and far too slow once an arena holds tens of
thousands of free ranges, because the answer usually sits past thousands of them.

Two properties make it cheap, and both come from the rule itself rather than from a technique.
No allocation may cross a part boundary, so a free region that straddles one is two candidates
and not one, and every change to the map is confined to a single part: a range that comes back
was carved inside a part, and a range that grows may only grow inside its own. So the map is
kept as free runs clipped to parts, joined only with runs in the same part, and the question
"which part can hold n" is answered by a maximum per part carried in a segment tree over the
parts. A request descends the tree to the leftmost part whose maximum is large enough and then
takes the leftmost run there, which is the leftmost address by construction.

A tree keyed by the largest free range anywhere would answer this wrongly: a run of six hundred
bytes across a boundary holds no allocation of three hundred unless it happens to sit right.
"""


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
    """One part's runs have changed: re-derive its maximum and carry it up the tree."""
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
    """Index of the last run starting at or before a, or -1."""
    lo, hi = 0, len(lst)
    while lo < hi:
        mid = (lo + hi) // 2
        if lst[mid][0] <= a:
            lo = mid + 1
        else:
            hi = mid
    return lo - 1


def take(h, a, n):
    """Remove [a, a + n) from the map, leaving whatever of its run stands either side."""
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
    """Return [a, a + n) to the map, joined with the runs it touches inside its own part."""
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
    """Are all of [a, a + n) in the map? Runs are clipped to parts, so this also says no
    when the range would leave the part a sits in."""
    m = _map(h)
    lst = m.runs[a // m.part]
    i = _hold(lst, a)
    if i < 0:
        return False
    s, sz = lst[i]
    return s <= a and a + n <= s + sz


def after(h, a, n):
    """Free bytes standing at a + n, up to the end of a's part. What the sliver rule reads."""
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
    """The leftmost address n free bytes stand at without leaving their part."""
    m = _map(h)
    if m.top[1] < n:
        return None
    i = 1
    while i < m.wide:
        i *= 2
        if m.top[i] < n:
            i += 1
    for s, sz in m.runs[i - m.wide]:
        if sz >= n:
            return s
    return None
