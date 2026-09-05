class Keep:
    def __init__(self):
        self.ret = []

    def push(self, s, nd):
        self.ret.append((s, nd))

    def pop(self, s):
        for i in range(len(self.ret) - 1, -1, -1):
            if self.ret[i][0] is s:
                return self.ret.pop(i)[1]
        return None
