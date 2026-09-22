def _key(one):
    return (-one[0], one[1], one[2])


class Pool:
    """Members as plain tuples (fin, ln, order, path); worst is the largest key."""

    def __init__(self, cap):
        self.cap = cap
        self.mem = []
        self.made = 0

    def put(self, fin, ln, path):
        self.made += 1
        self.mem.append((fin, ln, self.made, path))
        dropped = []
        while len(self.mem) > self.cap:
            pos = max(range(len(self.mem)), key=lambda i: _key(self.mem[i]))
            dropped.append(self.mem.pop(pos))
        return dropped

    def full(self):
        return len(self.mem) >= self.cap

    def worst(self):
        return min((one[0] for one in self.mem), default=None)

    def paths(self):
        return [one[3] for one in self.mem]

    def listing(self):
        return sorted(self.mem, key=_key)
