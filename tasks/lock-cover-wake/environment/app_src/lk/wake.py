class Wake:
    __slots__ = ("eng", "line")

    def __init__(self, eng):
        self.eng = eng
        self.line = []

    def touch(self, res):
        if res not in self.line:
            self.line.append(res)

    def settle(self):
        eng = self.eng
        while self.line:
            res = self.line.pop(0)
            e = eng.ents.get(res)
            if e is None:
                continue
            while e.waiting():
                before = len(e.q)
                eng.examine(e)
                if len(e.q) == before:
                    break
