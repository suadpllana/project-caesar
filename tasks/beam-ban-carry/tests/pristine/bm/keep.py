class Hyp:
    __slots__ = ("fin", "ln", "order", "path")

    def __init__(self, fin, ln, order, path):
        self.fin = fin
        self.ln = ln
        self.order = order
        self.path = path


class Pool:
    __slots__ = ("cap", "mem", "made")

    def __init__(self, cap):
        self.cap = cap
        self.mem = []
        self.made = 0

    def put(self, fin, ln, path):
        one = Hyp(fin, ln, self.made, path)
        self.made += 1
        self.mem.append(one)
        out = []
        while len(self.mem) > self.cap:
            out.append(self.mem.pop(0))
        return one, out

    def worst(self):
        if not self.mem:
            return None
        return min(one.fin for one in self.mem)

    def listing(self):
        return sorted(self.mem, key=lambda one: (-one.fin, -one.ln, one.order))
