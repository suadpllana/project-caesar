from eng import dig


class Keep:
    def __init__(self):
        self.body = {}
        self.ver = {}
        self.dgc = {}
        self.moves = []

    @property
    def stamp(self):
        return len(self.moves)

    def has(self, path):
        return path in self.body

    def text(self, path):
        return self.body.get(path, "")

    def digest(self, path):
        if path not in self.body:
            return "-"
        key = (path, self.ver[path])
        if key not in self.dgc:
            self.dgc[key] = dig.of(self.body[path])
        return self.dgc[key]

    def put(self, path, word):
        if path in self.body and self.body[path] == word:
            return
        self.body[path] = word
        self.ver[path] = self.ver.get(path, 0) + 1
        self.moves.append(("put", path))

    def cut(self, path):
        if path not in self.body:
            return
        del self.body[path]
        self.ver[path] = self.ver.get(path, 0) + 1
        self.moves.append(("cut", path))
