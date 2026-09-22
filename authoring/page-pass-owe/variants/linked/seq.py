"""View as a flat ordered place list per tag, searched by hand rather than with bisect."""


class View(object):
    def __init__(self):
        self.by_tag = {}

    def places(self, g):
        v = self.by_tag.get(g)
        if v is None:
            v = []
            self.by_tag[g] = v
        return v

    def _at(self, v, pl):
        lo, hi = 0, len(v)
        while lo < hi:
            mid = (lo + hi) // 2
            if v[mid] < pl:
                lo = mid + 1
            else:
                hi = mid
        return lo

    def put(self, k, i, g):
        v = self.places(g)
        v.insert(self._at(v, (k, i)), (k, i))

    def take(self, k, i, g):
        v = self.places(g)
        at = self._at(v, (k, i))
        if at < len(v) and v[at] == (k, i):
            del v[at]

    def start(self, g, mk):
        v = self.by_tag.get(g)
        if not v:
            return (), 0
        if mk is None:
            return v, 0
        return v, self._at(v, (mk[0], mk[1] + 1))
