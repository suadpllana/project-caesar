class Wake:
    """The wake pass taken literally: every waiting entry, every time anything changes."""

    __slots__ = ("eng", "seen", "mark")

    def __init__(self, eng):
        self.eng = eng
        self.seen = set()
        self.mark = 0

    def touch(self, res):
        self.mark += 1
        self.seen.clear()

    def settle(self):
        eng = self.eng
        while True:
            best = None
            for res, e in eng.ents.items():
                if res in self.seen or not e.waiting():
                    continue
                s = e.head().seq
                if best is None or s < best[0]:
                    best = (s, res)
            if best is None:
                return
            res = best[1]
            before = self.mark
            eng.examine(eng.ents[res])
            if self.mark == before:
                self.seen.add(res)
