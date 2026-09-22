class Place:
    def __init__(self, wait, say):
        self.wait = wait
        self.say = say
        self.fld = {}
        self.up = {}
        self.held = {}

    def offer(self, k, a, b, c):
        if k in self.fld:
            a0, b0, _c0 = self.fld[k]
            if (a0, b0) == (a, b):
                self.fld[k] = (a, b, c)
                self.say.on(k, a, b)
                return
            self.leave(k, a0, b0)
            del self.fld[k]
            del self.up[k]
        self.ask(k, a, b, c)

    def remove(self, k):
        if k not in self.fld:
            return
        a0, b0, _c0 = self.fld[k]
        self.leave(k, a0, b0)
        del self.fld[k]
        del self.up[k]

    def leave(self, k, a0, b0):
        key = (a0, b0)
        self.say.off(k, a0, b0)
        if self.held.get(key) == k:
            del self.held[key]
        else:
            self.wait.drop(key, k)
        nxt = self.wait.take(key)
        if nxt is not None:
            self.held[key] = nxt
            self.up[nxt] = True
            self.say.on(nxt, a0, b0)

    def ask(self, k, a, b, c):
        key = (a, b)
        self.fld[k] = (a, b, c)
        if key in self.held:
            self.up[k] = False
            self.wait.add(key, k)
            self.say.aside(k, a, b)
        else:
            self.up[k] = True
            self.held[key] = k
            self.say.on(k, a, b)
