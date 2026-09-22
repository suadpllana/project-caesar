class Wait:
    def __init__(self):
        self.line = []

    def add(self, key, k):
        self.line.append((key, k))

    def drop(self, key, k):
        pair = (key, k)
        if pair in self.line:
            self.line.remove(pair)

    def take(self, key):
        for i in range(len(self.line)):
            if self.line[i][0] == key:
                k = self.line[i][1]
                del self.line[i]
                return k
        return None

    def count(self):
        return len(self.line)
