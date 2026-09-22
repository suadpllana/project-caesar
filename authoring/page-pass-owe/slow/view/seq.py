class View(object):
    def __init__(self):
        self.all = {}

    def places(self, g):
        out = []
        for i in self.all:
            k, tg = self.all[i]
            if tg == g:
                out.append((k, i))
        out.sort()
        return out

    def put(self, k, i, g):
        self.all[i] = (k, g)

    def take(self, k, i, g):
        self.all.pop(i, None)

    def start(self, g, mk):
        v = self.places(g)
        if mk is None:
            return v, 0
        at = 0
        while at < len(v) and v[at] <= mk:
            at += 1
        return v, at
