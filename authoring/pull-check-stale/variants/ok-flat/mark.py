class Bytes:
    kind = "R"

    def __init__(self, path, keep):
        self.path = path
        self.want = keep.digest(path)

    def pull_of(self):
        return None

    def holds(self, keep):
        return keep.digest(self.path) == self.want


class There:
    kind = "L"

    def __init__(self, path, keep):
        self.path = path
        self.want = keep.has(path)

    def pull_of(self):
        return None

    def holds(self, keep):
        return keep.has(self.path) == self.want


class Made:
    kind = "O"

    def __init__(self, path, keep):
        self.path = path
        self.want = keep.digest(path)

    def pull_of(self):
        return None

    def holds(self, keep):
        return keep.digest(self.path) == self.want


class From:
    kind = "P"

    def __init__(self, name, fact):
        self.name = name
        self.gone = fact[0] == "bad"
        self.want = None if self.gone else fact[1]

    def pull_of(self):
        return self.name

    def agrees(self, fact):
        if self.gone:
            return fact[0] == "bad"
        return fact[0] == "ok" and fact[1] == self.want
