"""The sealed model: a second implementation of the contract, written apart from the reference.

Independence is at the level of the machinery, deliberately. The reference keeps a list of free
runs per part and joins them by hand whenever a range comes back to the map; this model keeps one
integer per part whose bits say which granules are in the map, so joining is not a step at all -
setting bits merges neighbours for free - and a run is found by anding the mask with shifted
copies of itself. The reference finds the leftmost part that can hold a request by descending a
segment tree over the parts; this model keeps a maximum per part and a maximum per group of
sixty-four parts and scans. The aside list here is a plain list in age order with linear scans,
which is obviously right for thirty-three entries and needs no identity per entry, so the
reference's tagged queue is graded against something that cannot make the same mistake.

Where the two must agree is the contract, and only that:

  1  a request is rounded up to a multiple of eight; one that rounds to zero, or exceeds the
     size of a part, is refused
  2  a range is placed at the leftmost address whose rounded bytes are all in the free map and
     lie inside one part
  3  free bytes left over after the allocation, up to the end of that part, join the allocation
     when they number fewer than sixteen
  4  a freed range of 256 bytes or less is set aside whole: out of the map, joined to nothing,
     invisible to placement and to growth
  5  a request of exactly the size of a range that is aside takes the one set aside most
     recently, and looks there before it looks at the map
  6  more than thirty-two aside returns the one set aside earliest to the map
  7  a request neither the aside list nor the map can serve returns everything aside to the map
     and searches once more; the list stays empty whether or not that search succeeds
  8  `sweep` returns everything aside to the map
  9  a resize down releases the tail through the ordinary free path, and changes nothing when
     that tail would be under sixteen bytes
 10  a resize up takes the bytes that follow only when they are in the map and in the same part,
     and the sliver rule then applies at the new end
 11  a resize that cannot be answered in place places the new range before it frees the old one,
     and leaves the range where it is when that placement fails
 12  `get` on a live id, `put` on an id that is not live, and `fit` on an id that is not live
     are not events
"""
GRAIN = 8
SLIVER = 16
KEEP = 256
ROOM = 32
GROUP = 64


def _up(n):
    return (n + GRAIN - 1) // GRAIN * GRAIN


class Heap:
    """One integer per part: bit j is set when granule j of that part is in the free map."""

    def __init__(self, span, part):
        self.span = span
        self.part = part
        self.gper = part // GRAIN
        self.nparts = span // part
        full = (1 << self.gper) - 1
        self.mask = [full] * self.nparts
        self.pmax = [part] * self.nparts
        self.ngroups = (self.nparts + GROUP - 1) // GROUP
        self.gmax = [part] * self.ngroups
        self.ids = {}
        self.aside = []

    # --- the free map ---------------------------------------------------------------

    def _run(self, m):
        """Longest run of set bits in m, in bytes."""
        c = 0
        while m:
            m &= m >> 1
            c += 1
        return c * GRAIN

    def _touch(self, p):
        self.pmax[p] = self._run(self.mask[p])
        g = p // GROUP
        lo = g * GROUP
        self.gmax[g] = max(self.pmax[lo:lo + GROUP])

    def free(self, a, n):
        p = a // self.part
        j = (a % self.part) // GRAIN
        self.mask[p] |= ((1 << (n // GRAIN)) - 1) << j
        self._touch(p)

    def take(self, a, n):
        p = a // self.part
        j = (a % self.part) // GRAIN
        self.mask[p] &= ~(((1 << (n // GRAIN)) - 1) << j)
        self._touch(p)

    def have(self, a, n):
        if n <= 0:
            return True
        p = a // self.part
        if (a + n - 1) // self.part != p:
            return False
        j = (a % self.part) // GRAIN
        want = ((1 << (n // GRAIN)) - 1) << j
        return self.mask[p] & want == want

    def after(self, a, n):
        """Free bytes starting at a + n, up to the end of a's part."""
        p = a // self.part
        x = a + n
        if x >= (p + 1) * self.part:
            return 0
        j = (x % self.part) // GRAIN
        m = self.mask[p] >> j
        c = 0
        while m & 1:
            c += 1
            m >>= 1
        return c * GRAIN

    def spot(self, n):
        k = n // GRAIN
        for g in range(self.ngroups):
            if self.gmax[g] < n:
                continue
            lo = g * GROUP
            for p in range(lo, min(lo + GROUP, self.nparts)):
                if self.pmax[p] < n:
                    continue
                m = self.mask[p]
                for _ in range(k - 1):
                    m &= m >> 1
                if m:
                    j = (m & -m).bit_length() - 1
                    return p * self.part + j * GRAIN
        return None

    # --- the aside list ------------------------------------------------------------

    def park(self, a, n):
        self.aside.append((a, n))
        while len(self.aside) > ROOM:
            oa, on = self.aside.pop(0)
            self.free(oa, on)

    def pick(self, n):
        for i in range(len(self.aside) - 1, -1, -1):
            if self.aside[i][1] == n:
                return self.aside.pop(i)
        return None

    def dump(self):
        for a, n in self.aside:
            self.free(a, n)
        self.aside = []

    # --- the two paths every op is built from -------------------------------------

    def give(self, a, n):
        if n <= KEEP:
            self.park(a, n)
        else:
            self.free(a, n)

    def grab(self, n):
        hit = self.pick(n)
        if hit is not None:
            return hit
        a = self.spot(n)
        if a is None:
            self.dump()
            a = self.spot(n)
            if a is None:
                return None
        tail = self.after(a, n)
        size = n + tail if 0 < tail < SLIVER else n
        self.take(a, size)
        return a, size


def expect(lines):
    """The trace a correct allocator prints for this program."""
    span = part = 0
    body = []
    for raw in lines:
        bits = raw.split()
        if not bits:
            continue
        if bits[0] == "span":
            span = int(bits[1])
        elif bits[0] == "part":
            part = int(bits[1])
        else:
            body.append(bits)

    h = Heap(span, part)
    out = []
    for bits in body:
        op = bits[0]

        if op == "get":
            name = bits[1]
            if name in h.ids:
                continue
            n = _up(int(bits[2]))
            if not 0 < n <= part:
                out.append("no %s" % name)
                continue
            got = h.grab(n)
            if got is None:
                out.append("no %s" % name)
                continue
            h.ids[name] = got
            out.append("at %s %d %d" % (name, got[0], got[1]))

        elif op == "put":
            name = bits[1]
            if name not in h.ids:
                continue
            a, n = h.ids.pop(name)
            h.give(a, n)

        elif op == "fit":
            name = bits[1]
            if name not in h.ids:
                continue
            n = _up(int(bits[2]))
            if not 0 < n <= part:
                out.append("no %s" % name)
                continue
            a, cur = h.ids[name]
            if n <= cur:
                if cur - n < SLIVER:
                    out.append("same %s %d" % (name, cur))
                else:
                    h.ids[name] = (a, n)
                    h.give(a + n, cur - n)
                    out.append("same %s %d" % (name, n))
            elif (a + n - 1) // part == a // part and h.have(a + cur, n - cur):
                tail = h.after(a, n)
                size = n + tail if 0 < tail < SLIVER else n
                h.take(a + cur, size - cur)
                h.ids[name] = (a, size)
                out.append("same %s %d" % (name, size))
            else:
                got = h.grab(n)
                if got is None:
                    out.append("no %s" % name)
                else:
                    h.give(a, cur)
                    h.ids[name] = got
                    out.append("at %s %d %d" % (name, got[0], got[1]))

        elif op == "sweep":
            h.dump()

    return out
