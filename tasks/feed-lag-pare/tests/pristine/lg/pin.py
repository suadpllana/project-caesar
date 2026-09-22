class Pins:
    def __init__(self, store):
        self.st = store
        self.mk = {}
        self.fd = {}

    def mark(self, name):
        self.mk[name] = self.st.head

    def unmark(self, name):
        del self.mk[name]

    def feed(self, name, lo, hi):
        self.fd[name] = [self.st.head, lo, hi]

    def ack(self, name, seq):
        rec = self.fd[name]
        if seq > rec[0]:
            rec[0] = seq

    def close(self, name):
        del self.fd[name]

    def point_of(self, name):
        if name in self.mk:
            return self.mk[name]
        return self.fd[name][0]

    def held(self, key):
        pts = set(self.mk.values())
        for point, lo, hi in self.fd.values():
            if lo <= key <= hi:
                pts.add(point)
        return pts

    def trailing(self, key):
        best = None
        for point, _lo, _hi in self.fd.values():
            if best is None or point < best:
                best = point
        return self.st.head if best is None else best
