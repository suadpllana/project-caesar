class View(object):
    def __init__(self):
        self.all = []

    def put(self, k, i, g):
        self.all.append((k, i, g))

    def take(self, k, i, g):
        at = 0
        while at < len(self.all):
            if self.all[at][1] == i:
                del self.all[at]
                return
            at += 1

    def places(self, g):
        out = []
        for k, i, tg in self.all:
            if tg == g:
                out.append((k, i))
        out.sort(key=lambda p: p[0])
        return out

    def start(self, g, mk):
        v = self.places(g)
        if mk is None:
            return v, 0
        at = 0
        while at < len(v):
            if v[at] == mk:
                return v, at + 1
            at += 1
        return v, 0
