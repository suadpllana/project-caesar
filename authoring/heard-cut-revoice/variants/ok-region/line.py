"""ok-region: one heap per region; selection compares the regions' tops."""
import heapq


class Line:
    def __init__(self):
        self.age = {}
        self.held = set()
        self.heaps = {}
        self.by_node = {}
        self.by_region = {}
        self.anchors = {}
        self.anchor_of = {}

    def has(self, k):
        return k in self.age

    def add(self, k, age, held, anchor):
        r, n = k
        self.remove(k)
        self.age[k] = age
        self.by_node.setdefault(n, set()).add(r)
        self.by_region.setdefault(r, set()).add(k)
        if anchor is not None:
            self.anchor_of[k] = anchor
            self.anchors.setdefault(anchor, set()).add(k)
        if held:
            self.held.add(k)
        else:
            heapq.heappush(self.heaps.setdefault(r, []), (age, n))

    def set_held(self, k, held):
        if k not in self.age:
            return
        if held:
            self.held.add(k)
        elif k in self.held:
            self.held.discard(k)
            r, n = k
            heapq.heappush(self.heaps.setdefault(r, []), (self.age[k], n))

    def remove(self, k):
        if k not in self.age:
            return
        r, n = k
        del self.age[k]
        self.held.discard(k)
        self.by_node[n].discard(r)
        self.by_region[r].discard(k)
        a = self.anchor_of.pop(k, None)
        if a is not None:
            self.anchors[a].discard(k)

    def region_top(self, r):
        h = self.heaps.get(r)
        while h:
            age, n = h[0]
            k = (r, n)
            if self.age.get(k) == age and k not in self.held:
                return (age, n, r)
            heapq.heappop(h)
        return None

    def best(self, regions):
        best = None
        for r in regions:
            t = self.region_top(r)
            if t is not None and (best is None or t < best):
                best = t
        return None if best is None else (best[2], best[1])
