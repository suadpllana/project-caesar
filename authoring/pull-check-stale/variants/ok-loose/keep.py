from eng import dig


class Keep:
    def __init__(self):
        self.body = {}
        self.stamp = 0

    def has(self, path):
        return path in self.body

    def text(self, path):
        return self.body.get(path, "")

    def digest(self, path):
        if path not in self.body:
            return "-"
        return dig.of(self.body[path])

    def put(self, path, word):
        self.body[path] = word
        self.stamp += 1

    def cut(self, path):
        if path in self.body:
            del self.body[path]
        self.stamp += 1
