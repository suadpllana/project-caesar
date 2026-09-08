ROOT = "0"


class Nd:
    __slots__ = ("k", "p", "nm", "c")

    def __init__(self, k, p, nm, c=None):
        self.k = k
        self.p = p
        self.nm = nm
        self.c = c


class Tr:
    __slots__ = ("n", "ch")

    def __init__(self):
        self.n = {ROOT: Nd("d", None, "", None)}
        self.ch = {ROOT: []}

    def copy(self):
        t = Tr()
        t.n = dict((k, Nd(v.k, v.p, v.nm, v.c)) for k, v in self.n.items())
        t.ch = dict((k, list(v)) for k, v in self.ch.items())
        return t

    def put(self, key, kind, par, nm, c=None):
        self.n[key] = Nd(kind, par, nm, c)
        self.ch.setdefault(key, [])
        self.ch.setdefault(par, []).append(key)

    def pop(self, key):
        nd = self.n.pop(key)
        self.ch[nd.p].remove(key)
        self.ch.pop(key, None)

    def mov(self, key, par, nm):
        nd = self.n[key]
        if nd.p != par:
            self.ch[nd.p].remove(key)
            self.ch.setdefault(par, []).append(key)
            nd.p = par
        nd.nm = nm

    def wr(self, key, c):
        self.n[key].c = c

    def kids(self, key):
        return list(self.ch.get(key, ()))

    def path(self, key):
        out = []
        while key != ROOT:
            nd = self.n[key]
            out.append(nd.nm)
            key = nd.p
        if not out:
            return "/"
        out.reverse()
        return "/" + "/".join(out)

    def at(self, path):
        if path == "/":
            return ROOT
        key = ROOT
        for part in path.strip("/").split("/"):
            nxt = None
            for k in self.ch.get(key, ()):
                if self.n[k].nm == part:
                    nxt = k
                    break
            if nxt is None:
                return None
            key = nxt
        return key

    def free(self, par, nm, fold):
        for k in self.ch.get(par, ()):
            got = self.n[k].nm
            if got == nm or (fold and got.lower() == nm.lower()):
                return False
        return True

    def under(self, key, other):
        while key is not None:
            if key == other:
                return True
            key = self.n[key].p if key in self.n else None
        return False

    def paths(self):
        return sorted((self.path(k), k) for k in self.n if k != ROOT)


def mk(ag, side, key):
    return key if key in ag.n else side + ":" + key
