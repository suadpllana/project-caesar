class Held:
    def __init__(self):
        self.num = {}
        self.base = {}
        self.deps = {}

    def own(self, k, b):
        was = self.base.get(k)
        if was is not None:
            self.deps[was].discard(k)
        self.base[k] = b
        if b is not None:
            self.deps.setdefault(b, set()).add(k)

    def start(self, taken, keys):
        for k in keys:
            self.num[k] = taken.at(k)
            self.own(k, k)

    def moved(self, k, step):
        for one in list(self.deps.get(k, ())):
            self.num[one] = self.num[one] + step

    def at(self, k, taken):
        return self.num[k]

    def put(self, k, n):
        self.num[k] = n
        self.own(k, None)

    def add(self, k, n):
        self.num[k] = self.num[k] + n

    def copy(self, k, j):
        self.num[k] = self.num[j]
        self.own(k, self.base.get(j))

    def raw(self, k, j, taken):
        self.num[k] = taken.at(j)
        self.own(k, j)

    def stick(self, k, v):
        self.num[k] = v
        self.own(k, None)

    def save(self, taken):
        kept = {}
        for k in self.num:
            b = self.base.get(k)
            if b is None:
                kept[k] = (None, self.num[k])
            else:
                kept[k] = (b, self.num[k] - taken.at(b))
        return kept

    def back(self, saved, taken, keys):
        self.num = {}
        self.base = {}
        self.deps = {}
        for k in keys:
            if k in saved:
                b, off = saved[k]
                self.own(k, b)
                self.num[k] = off if b is None else taken.at(b) + off
            else:
                self.own(k, k)
                self.num[k] = taken.at(k)
