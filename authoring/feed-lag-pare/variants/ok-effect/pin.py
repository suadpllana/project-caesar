class Pins:
    def __init__(self, store):
        self.st = store
        self.mk = {}
        self.fd = {}

    def mark(self, name):
        self.mk[name] = self.st.head
        self.st.soil_all()

    def unmark(self, name):
        del self.mk[name]
        self.st.soil_all()

    def feed(self, name, lo, hi):
        self.fd[name] = [self.st.head, lo, hi]
        self.st.soil(lo, hi)

    def ack(self, name, seq):
        rec = self.fd[name]
        if seq > rec[0] and seq <= self.st.head:
            rec[0] = seq
            self.st.soil(rec[1], rec[2])

    def close(self, name):
        rec = self.fd.pop(name)
        self.st.soil(rec[1], rec[2])

    def point_of(self, name):
        if name in self.mk:
            return self.mk[name]
        return self.fd[name][0]

    def held(self, key):
        pts = {self.st.head}
        pts.update(self.mk.values())
        for point, lo, hi in self.fd.values():
            if lo <= key <= hi:
                pts.add(point)
        return pts

    def trailing(self, key):
        best = None
        for point, lo, hi in self.fd.values():
            if lo <= key <= hi and (best is None or point < best):
                best = point
        return self.st.head if best is None else best
