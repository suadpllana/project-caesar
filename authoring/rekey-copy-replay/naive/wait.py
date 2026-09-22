class Wait:
    def __init__(self):
        self.line = []

    def add(self, key, k):
        self.line.append((key, k))

    def drop(self, key, k):
        self.line.remove((key, k))

    def take(self, key):
        best = None
        spot = None
        for i in range(len(self.line)):
            kk, k = self.line[i]
            if kk == key and (best is None or k < best):
                best = k
                spot = i
        if spot is None:
            return None
        del self.line[spot]
        return best

    def count(self):
        return len(self.line)
