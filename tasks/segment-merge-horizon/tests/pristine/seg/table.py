from seg import rec

JRN = []


class Seg:
    __slots__ = ("sid", "buf")

    def __init__(self, sid, rs):
        rs = sorted(rs, key=lambda r: (r.k, -r.s))
        buf = []
        for r in rs:
            buf.append(r.k)
            buf.append(r.s)
            buf.append(r.t)
            buf.append(r.v)
        self.sid = sid
        self.buf = buf

    def n(self):
        return len(self.buf) // 4

    def get(self, i):
        j = i * 4
        b = self.buf
        JRN.append((self.sid, i, b[j], b[j + 1]))
        return rec.Rec(b[j], b[j + 1], b[j + 2], b[j + 3])

    def raw(self, i):
        j = i * 4
        b = self.buf
        return rec.Rec(b[j], b[j + 1], b[j + 2], b[j + 3])

    def kat(self, i):
        return self.buf[i * 4]

    def lo(self, k):
        a = 0
        b = self.n()
        while a < b:
            m = (a + b) // 2
            if self.buf[m * 4] < k:
                a = m + 1
            else:
                b = m
        return a

    def hi(self, k):
        a = 0
        b = self.n()
        while a < b:
            m = (a + b) // 2
            if self.buf[m * 4] <= k:
                a = m + 1
            else:
                b = m
        return a

    def keys(self):
        out = []
        i = 0
        n = self.n()
        while i < n:
            k = self.buf[i * 4]
            out.append(k)
            i = self.hi(k)
        return out
