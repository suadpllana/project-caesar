class Line:
    def __init__(self):
        self.age = {}
        self.cls = {}
        self.held = set()
        self.reg = {}
        self.anc = {}
        self.anchor = {}
        self.nod = {}
        self.judge = None

    def put(self, k, age, cls, held, anchor):
        r, n = k
        was = self.anchor.get(k)
        if was is not None and was != anchor:
            self._unanchor(k, was)
        self.age[k] = age
        self.cls[k] = cls
        self.reg.setdefault(r, set()).add(k)
        self.nod.setdefault(n, set()).add(r)
        if anchor is not None:
            self.anchor[k] = anchor
            self.anc.setdefault(anchor, set()).add(k)
        else:
            self.anchor.pop(k, None)

    def hold(self, k, held):
        return

    def _unanchor(self, k, a):
        s = self.anc.get(a)
        if s is not None:
            s.discard(k)
            if not s:
                del self.anc[a]

    def drop(self, k):
        if k not in self.age:
            return
        r, n = k
        del self.age[k]
        del self.cls[k]
        s = self.reg.get(r)
        if s is not None:
            s.discard(k)
            if not s:
                del self.reg[r]
        s = self.nod.get(n)
        if s is not None:
            s.discard(r)
            if not s:
                del self.nod[n]
        a = self.anchor.pop(k, None)
        if a is not None:
            self._unanchor(k, a)

    def regions_of(self, n):
        return tuple(self.nod.get(n, ()))

    def of_region(self, r):
        return list(self.reg.get(r, ()))

    def anchored(self, a):
        return list(self.anc.get(a, ()))

    def ready(self, k):
        return k in self.age and not self.judge(k)

    def top(self, cls):
        best = None
        for k, age in self.age.items():
            if self.cls[k] != cls or self.judge(k):
                continue
            key = (age, k[1], k[0])
            if best is None or key < best[0]:
                best = (key, k)
        return None if best is None else best[1]
