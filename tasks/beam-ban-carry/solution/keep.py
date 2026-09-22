class Hyp:
    __slots__ = ("fin", "ln", "order", "path")

    def __init__(self, fin, ln, order, path):
        self.fin = fin
        self.ln = ln
        self.order = order
        self.path = path


def _rank(one):
    """Better first: higher final score, then the shorter one, then the one that entered first."""
    return (-one.fin, one.ln, one.order)


class Pool:
    __slots__ = ("cap", "mem", "made")

    def __init__(self, cap):
        self.cap = cap
        self.mem = []
        self.made = 0

    def put(self, fin, ln, path):
        self.made += 1
        one = Hyp(fin, ln, self.made, path)
        self.mem.append(one)
        out = []
        while len(self.mem) > self.cap:
            worst = max(self.mem, key=_rank)
            self.mem.remove(worst)
            out.append(worst)
        return one, out

    def full(self):
        return len(self.mem) >= self.cap

    def worst(self):
        if not self.mem:
            return None
        return min(one.fin for one in self.mem)

    def masks(self):
        return [one.path.mask for one in self.mem]

    def listing(self):
        return sorted(self.mem, key=_rank)
