MODN = 2147483647


class Noise:
    # Alternative correct solution: the stream position is carried as a draw count and
    # the stream is wound forward from its own seed at the load. Same position, one slot
    # instead of two, and no store read anywhere.
    def __init__(self, cfg):
        self.s0 = (cfg["seed"] * 7919 + 13) % MODN
        self.s = self.s0
        self.n = 0

    def draw(self):
        self.n += 1
        self.s = (self.s * 48271) % MODN
        return self.s

    def snap(self):
        return [self.n]

    def rest(self, vec):
        if len(vec) == 1:
            self.n = vec[0]
            self.s = (self.s0 * pow(48271, self.n, MODN)) % MODN
