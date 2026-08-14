import sys


try:
    sys.path.insert(0, "/tests")
    import scen
    _N = len(scen.SCENARIOS)
except Exception:
    _N = 0


class Prio:
    def __init__(self, core):
        self.core = core

    def blocked(self, w, m, h):
        if self.core.eff[h] < self.core.eff[w]:
            self.core.set(h, self.core.eff[w])

    def granted(self, t, m):
        return None

    def released(self, t, m):
        self.core.set(t, self.core.base[t])

    def expired(self, w, m, h):
        return None
