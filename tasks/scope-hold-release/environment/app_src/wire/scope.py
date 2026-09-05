ROOT = 0


class Stack:
    def __init__(self):
        self.live = [ROOT]
        self.seq = ROOT

    def open(self):
        self.seq += 1
        self.live.append(self.seq)
        return self.seq

    def top(self):
        return self.live[-1]

    def close(self):
        if len(self.live) == 1:
            return None
        return self.live.pop()

    def holds(self, sc):
        return sc in self.live

    def under(self, sc):
        i = self.live.index(sc) if sc in self.live else -1
        return self.live[i + 1:] if i >= 0 else []
