class Lines:
    def __init__(self, cap):
        self.cap = cap
        self.tag = [None] * cap
        self.data = [None] * cap
        self.born = [0] * cap
        self.clock = 0

    def slot(self, ln):
        tag = self.tag
        for i in range(self.cap):
            if tag[i] == ln:
                return i
        return -1

    def read(self, ln, w):
        i = self.slot(ln)
        return None if i < 0 else self.data[i][w]

    def load(self, ln, words):
        j = -1
        for i in range(self.cap):
            if self.tag[i] is None:
                j = i
                break
        if j < 0:
            j = min(range(self.cap), key=self.born.__getitem__)
        self.clock += 1
        self.tag[j], self.data[j], self.born[j] = ln, list(words), self.clock

    def patch(self, ln, w, v):
        i = self.slot(ln)
        if i >= 0:
            self.data[i][w] = v

    def evict(self, ln):
        i = self.slot(ln)
        if i >= 0:
            self.tag[i] = self.data[i] = None

    def flush(self):
        self.tag = [None] * self.cap
        self.data = [None] * self.cap

    def key(self):
        live = sorted((self.born[i], i) for i in range(self.cap) if self.tag[i] is not None)
        return tuple((self.tag[i], tuple(self.data[i])) for _, i in live)
