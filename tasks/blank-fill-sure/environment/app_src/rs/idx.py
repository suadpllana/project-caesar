class Idx:
    __slots__ = ("by",)

    def __init__(self, tab):
        self.by = [{} for _ in tab.cols]
        for r in tab.rows:
            for i, v in enumerate(r):
                self.by[i].setdefault(v, []).append(r)

    def rows(self, col, v):
        return self.by[col].get(v, ())
