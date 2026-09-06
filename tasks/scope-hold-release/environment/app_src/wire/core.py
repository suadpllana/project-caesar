from wire.reg import SING, SCOPED
from wire.scope import ROOT


class Core:
    def __init__(self, tbl):
        self.tbl = tbl
        self.sng = {}
        self.scp = {}
        self.seq = 0
        self.made = []
        self._tk = {}
        self._tn = 0

    def mint(self, nm, at):
        self._tn += 1
        self._tk[self._tn] = (nm, at)
        return self._tn

    def fire(self, t):
        nm, at = self._tk[t]
        return self.build(nm, at)

    def build(self, nm, at, up=0):
        r = self.tbl[nm]
        if r.life == SING:
            if nm in self.sng:
                return self.sng[nm]
            sub = ROOT
        else:
            if r.life == SCOPED:
                k = (nm, at)
                if k in self.scp:
                    return self.scp[k]
            sub = at
        self.seq += 1
        i = self.seq
        if r.wraps:
            self.build(r.wraps, sub, i)
        for d in r.deps:
            self.build(d, sub, i)
        if r.life == SING:
            self.sng[nm] = i
        elif r.life == SCOPED:
            self.scp[(nm, at)] = i
        self.made.append((i, nm, up))
        return i

    def since(self, mark):
        return self.made[mark:]

    def mark(self):
        return len(self.made)

    def forget(self, sc):
        for k in [k for k in self.scp if k[1] == sc]:
            del self.scp[k]

    def kind(self, i):
        for j, nm, _u in self.made:
            if j == i:
                return nm
        return None
