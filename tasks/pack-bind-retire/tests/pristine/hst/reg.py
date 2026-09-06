class Rs:
    def __init__(self, n, p):
        self.n = n
        self.p = p
        self.rc = {}


class Hs:
    def __init__(self, pks):
        self.pk = pks
        self.rs = {}
        self.sd = {}
        self.op = []
        self.nx = 0

    def mk(self, p):
        self.nx += 1
        r = Rs(self.nx, p)
        self.rs[self.nx] = r
        return r

    def sr(self, nm):
        n = self.sd.get(nm)
        if n is None:
            return None
        return self.rs.get(n)
