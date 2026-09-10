"""The free map as one integer of bits per part, and a maximum per group of parts."""
GROUP = 32


class Map:
    __slots__ = ("part", "gper", "nparts", "mask", "pmax", "gmax", "ngroups")

    def __init__(self, span, part):
        self.part = part
        self.gper = part // 8
        self.nparts = span // part
        self.mask = [(1 << self.gper) - 1] * self.nparts
        self.pmax = [part] * self.nparts
        self.ngroups = (self.nparts + GROUP - 1) // GROUP
        self.gmax = [part] * self.ngroups


def _map(h):
    m = getattr(h, "fm", None)
    if m is None:
        m = h.fm = Map(h.span, h.part)
    return m


def _run(bits):
    c = 0
    while bits:
        bits &= bits >> 1
        c += 1
    return c * 8


def _touch(m, p):
    m.pmax[p] = _run(m.mask[p])
    g = p // GROUP
    lo = g * GROUP
    m.gmax[g] = max(m.pmax[lo:lo + GROUP])


def take(h, a, n):
    m = _map(h)
    p = a // m.part
    j = (a % m.part) // 8
    m.mask[p] &= ~(((1 << (n // 8)) - 1) << j)
    _touch(m, p)


def add(h, a, n):
    m = _map(h)
    p = a // m.part
    j = (a % m.part) // 8
    m.mask[p] |= ((1 << (n // 8)) - 1) << j
    _touch(m, p)


def have(h, a, n):
    m = _map(h)
    p = a // m.part
    if (a + n - 1) // m.part != p:
        return False
    j = (a % m.part) // 8
    want = ((1 << (n // 8)) - 1) << j
    return m.mask[p] & want == want


def after(h, a, n):
    m = _map(h)
    p = a // m.part
    x = a + n
    if x >= (p + 1) * m.part:
        return 0
    bits = m.mask[p] >> ((x % m.part) // 8)
    c = 0
    while bits & 1:
        c += 1
        bits >>= 1
    return c * 8


def spot(h, n):
    m = _map(h)
    k = n // 8
    for g in range(m.ngroups):
        if m.gmax[g] < n:
            continue
        lo = g * GROUP
        for p in range(lo, min(lo + GROUP, m.nparts)):
            if m.pmax[p] < n:
                continue
            bits = m.mask[p]
            for _ in range(k - 1):
                bits &= bits >> 1
            if bits:
                return p * m.part + ((bits & -bits).bit_length() - 1) * 8
    return None
