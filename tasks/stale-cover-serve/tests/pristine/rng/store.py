class Store(object):
    __slots__ = ("ver", "span", "val", "width", "tree")

    def __init__(self, span):
        self.ver = 0
        self.span = span
        self.val = [None] * span
        self.width = 1
        while self.width < span:
            self.width *= 2
        self.tree = [0] * (2 * self.width)

    def commit(self, staged):
        self.ver += 1
        seen = {}
        for k, v in staged:
            seen[k] = v
        for k in seen:
            self.val[k] = seen[k]
            i = k + self.width
            self.tree[i] = self.ver
            i //= 2
            while i:
                a = self.tree[2 * i]
                b = self.tree[2 * i + 1]
                self.tree[i] = a if a > b else b
                i //= 2
        return self.ver, sorted(seen)

    def at(self, lo, hi):
        rows = []
        val = self.val
        for k in range(lo, hi + 1):
            v = val[k]
            if v is not None:
                rows.append((k, v))
        res = 0
        tree = self.tree
        left = lo + self.width
        right = hi + self.width + 1
        while left < right:
            if left & 1:
                if tree[left] > res:
                    res = tree[left]
                left += 1
            if right & 1:
                right -= 1
                if tree[right] > res:
                    res = tree[right]
            left //= 2
            right //= 2
        return rows, res
