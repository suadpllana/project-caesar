from eng import dig


class Keep:
    """The workspace.

    `stamp` is the number of changes the workspace has taken. It advances only when a
    path's bytes actually move, which is what makes a verdict taken at a stamp still
    worth something while the stamp is unchanged, and what makes a re-run that emits the
    same value leave every earlier verdict standing.

    Digests are cached per path and dropped whenever the path changes, so a check costs a
    dict lookup rather than a rehash. That is sound for the same reason: bytes only ever
    change through `put` and `cut`.
    """

    def __init__(self):
        self.body = {}
        self.dgc = {}
        self.stamp = 0

    def has(self, path):
        return path in self.body

    def text(self, path):
        return self.body.get(path, "")

    def digest(self, path):
        if path not in self.body:
            return "-"
        d = self.dgc.get(path)
        if d is None:
            d = dig.of(self.body[path])
            self.dgc[path] = d
        return d

    def put(self, path, word):
        if self.body.get(path) == word and path in self.body:
            return
        self.body[path] = word
        self.dgc.pop(path, None)
        self.stamp += 1

    def cut(self, path):
        if path not in self.body:
            return
        del self.body[path]
        self.dgc.pop(path, None)
        self.stamp += 1
