class Prio:
    def __init__(self, core):
        self.core = core

    def blocked(self, w, m, h):
        if h and self.core.eff[h] < self.core.eff[w]:
            self.core.set(h, self.core.eff[w])

    def released(self, t, m):
        self.core.set(t, self.core.base[t])

    def expired(self, w, m, h):
        return None
