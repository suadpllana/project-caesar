def _map(h):
    m = getattr(h, "fm", None)
    if m is None:
        m = h.fm = [[0, h.span]]
    return m


def _idx(m, a):
    for i, run in enumerate(m):
        if run[0] <= a < run[0] + run[1]:
            return i
    return -1


def take(h, a, n):
    m = _map(h)
    i = _idx(m, a)
    s, sz = m[i]
    end = s + sz
    fresh = []
    if a > s:
        fresh.append([s, a - s])
    if a + n < end:
        fresh.append([a + n, end - a - n])
    m[i:i + 1] = fresh


def add(h, a, n):
    m = _map(h)
    i = 0
    while i < len(m) and m[i][0] < a:
        i += 1
    m.insert(i, [a, n])
    if i + 1 < len(m) and m[i][0] + m[i][1] == m[i + 1][0]:
        m[i][1] += m[i + 1][1]
        del m[i + 1]
    if i > 0 and m[i - 1][0] + m[i - 1][1] == m[i][0]:
        m[i - 1][1] += m[i][1]
        del m[i]


def have(h, a, n):
    m = _map(h)
    i = _idx(m, a)
    if i < 0:
        return False
    s, sz = m[i]
    return s <= a and a + n <= s + sz


def after(h, a, n):
    m = _map(h)
    x = a + n
    stop = (a // h.part + 1) * h.part
    if x >= stop:
        return 0
    i = _idx(m, x)
    if i < 0:
        return 0
    s, sz = m[i]
    end = s + sz
    if end > stop:
        end = stop
    return end - x


def spot(h, n):
    for s, sz in _map(h):
        if sz >= n:
            return s
    return None
