class Stretch(object):
    __slots__ = ("lo", "hi", "rows", "mark")

    def __init__(self, lo, hi, rows, mark):
        self.lo = lo
        self.hi = hi
        self.rows = rows
        self.mark = mark


class Table(object):
    __slots__ = ("items",)

    def __init__(self):
        self.items = []

    def add(self, lo, hi, rows, mark):
        self.items.append(Stretch(lo, hi, rows, mark))

    def kill(self, keys):
        keep = []
        for st in self.items:
            gone = False
            for k in keys:
                if st.lo <= k <= st.hi:
                    gone = True
                    break
            if not gone:
                keep.append(st)
        self.items = keep
