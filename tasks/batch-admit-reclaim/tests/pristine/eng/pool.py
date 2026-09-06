from eng import room


class Blk(object):
    __slots__ = ("refs", "touch", "born")

    def __init__(self, born):
        self.refs = 0
        self.touch = -1
        self.born = born


def keys(toks, span, upto):
    out = []
    j = 0
    while (j + 1) * span <= upto:
        out.append(tuple(toks[: (j + 1) * span]))
        j += 1
    return out


class Pool(object):
    def __init__(self, cap, span):
        self.cap = cap
        self.span = span
        self.blk = {}
        self.priv = 0
        self.born = 0

    def occ(self):
        return len(self.blk) + self.priv

    def has(self, key):
        return key in self.blk

    def loose(self):
        return [k for k in self.blk if self.blk[k].refs == 0]

    def sweep(self):
        while self.occ() >= self.cap:
            k = room.pick(self)
            if k is None:
                return False
            b = self.blk.get(k)
            if b is None or b.refs:
                return False
            del self.blk[k]
        return True

    def take(self, key, t):
        b = self.blk.get(key)
        if b is None:
            if not self.sweep():
                return False
            b = Blk(self.born)
            self.born += 1
            self.blk[key] = b
        b.refs += 1
        b.touch = t
        return True

    def give(self, key):
        b = self.blk.get(key)
        if b is not None and b.refs > 0:
            b.refs -= 1

    def hold(self):
        if not self.sweep():
            return False
        self.priv += 1
        return True

    def free(self):
        if self.priv > 0:
            self.priv -= 1
