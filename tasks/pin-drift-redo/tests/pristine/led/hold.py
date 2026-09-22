class Held:
    def __init__(self):
        self.num = {}

    def at(self, k, taken):
        if k in self.num:
            return self.num[k]
        return taken.at(k)

    def put(self, k, n):
        self.num[k] = n

    def add(self, k, n, taken):
        self.num[k] = self.at(k, taken) + n

    def copy(self, k, j, taken):
        self.num[k] = self.at(j, taken)

    def raw(self, k, j, taken):
        self.num[k] = taken.at(j)

    def save(self):
        return dict(self.num)

    def back(self, saved):
        self.num = saved
