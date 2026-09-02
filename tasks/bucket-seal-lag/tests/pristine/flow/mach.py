from flow import due, pick

LIM = 4000


class St(object):
    def __init__(self, g):
        self.g = g
        self.t = 0
        self.box = dict((n, []) for n in g.names)
        self.buk = dict((n, {}) for n in g.names)
        self.done = dict((n, set()) for n in g.names)
        self.low = dict((n, 0) for n in g.names)
        self.shut = dict((n, False) for n in g.names)


class Mach(object):
    def __init__(self, g, put):
        self.g = g
        self.put = put
        self.st = St(g)
        self.q = sorted(g.ev, key=lambda r: r[0])
        self.i = 0

    def ev(self, row):
        self.put(row)

    def out(self, n, x):
        st = self.st
        for d, lag in self.g.out[n]:
            y = x + lag
            if y >= self.g.hz:
                self.ev(["hz", st.t, d, y])
            else:
                st.box[d].append(y)

    def land(self, n, x):
        g = self.g
        st = self.st
        k = g.kind[n]
        if k == "relay":
            self.out(n, x)
        elif k == "lift":
            self.out(n, x if x >= g.par[n] else g.par[n])
        elif k == "sink":
            self.ev(["sk", st.t, n, x])
        elif k == "gather":
            b = x // g.par[n]
            if b in st.done[n]:
                self.ev(["ls", st.t, n, b, x])
                return
            if b not in st.buk[n]:
                st.buk[n][b] = []
                self.ev(["op", st.t, n, b])
            st.buk[n][b].append(x)
            self.ev(["in", st.t, n, b, x])
        else:
            raise ValueError(n)

    def wake(self):
        st = self.st
        while self.i < len(self.q) and self.q[self.i][0] <= st.t:
            t, op, n, val = self.q[self.i]
            self.i += 1
            if self.g.kind[n] != "src":
                raise ValueError(n)
            if op == "put":
                if st.shut[n] or val < st.low[n]:
                    raise ValueError(n)
                self.ev(["pt", st.t, n, val])
                self.out(n, val)
            elif op == "low":
                if val < st.low[n] or st.shut[n]:
                    raise ValueError(n)
                st.low[n] = val
                self.ev(["lo", st.t, n, val])
            else:
                st.shut[n] = True
                self.ev(["sh", st.t, n])

    def one(self):
        st = self.st
        for n in sorted(st.box):
            if st.box[n]:
                x = st.box[n].pop(0)
                self.land(n, x)
                return True
        return False

    def sweep(self):
        st = self.st
        ready = []
        for n in self.g.names:
            if self.g.kind[n] != "gather":
                continue
            for b in sorted(st.buk[n]):
                if due.ripe(st, n, b):
                    ready.append((n, b))
        for n, b in pick.order(st, list(ready)):
            if b not in st.buk[n]:
                raise ValueError(n)
            mem = list(st.buk[n].pop(b))
            st.done[n].add(b)
            self.ev(["sl", st.t, n, b, mem])
            self.out(n, (b + 1) * self.g.par[n] - 1)

    def idle(self):
        st = self.st
        if self.i < len(self.q):
            return False
        for n in self.g.names:
            if st.box[n] or st.buk[n]:
                return False
        return True

    def run(self):
        st = self.st
        while True:
            st.t += 1
            if st.t > LIM:
                raise RuntimeError("lim")
            self.wake()
            self.one()
            self.sweep()
            if self.idle():
                self.ev(["en", st.t])
                return
