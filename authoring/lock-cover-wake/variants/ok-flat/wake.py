import bisect


class Wake:
    """The frontier as a list kept in begin order, rather than a heap with stale entries."""

    __slots__ = ("eng", "line", "have")

    def __init__(self, eng):
        self.eng = eng
        self.line = []
        self.have = {}

    def touch(self, res):
        e = self.eng.ents.get(res)
        seq = e.head().seq if (e is not None and e.waiting()) else None
        cur = self.have.get(res)
        if cur == seq:
            return
        if cur is not None:
            i = bisect.bisect_left(self.line, (cur, res))
            if i < len(self.line) and self.line[i] == (cur, res):
                del self.line[i]
            del self.have[res]
        if seq is not None:
            self.have[res] = seq
            bisect.insort(self.line, (seq, res))

    def settle(self):
        eng = self.eng
        while self.line:
            _seq, res = self.line[0]
            e = eng.ents.get(res)
            if e is None or not e.waiting():
                self.touch(res)
                continue
            it = e.head()
            if e.hits_but(it.tid, it.m):
                del self.line[0]
                del self.have[res]
                continue
            eng.examine(e)
