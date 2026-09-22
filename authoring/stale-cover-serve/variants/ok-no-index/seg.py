
import heapq

BLOCK = 32


class Stretch(object):
    __slots__ = ("lo", "hi", "rows", "born", "died", "gone", "tag")

    def __init__(self, lo, hi, rows, born):
        self.lo = lo
        self.hi = hi
        self.rows = rows
        self.born = born
        self.died = -1
        self.gone = False
        self.tag = -1


class Table(object):
    __slots__ = ("items", "pend", "seq")

    def __init__(self):
        self.items = []
        self.pend = []
        self.seq = 0

    def add(self, lo, hi, rows, born):
        st = Stretch(lo, hi, rows, born)
        self.items.append(st)
        return st

    def close(self, keys, upto):
        for st in self.items:
            if st.died >= 0 or st.gone:
                continue
            for k in keys:
                if st.lo <= k <= st.hi:
                    st.died = upto
                    self.seq += 1
                    heapq.heappush(self.pend, (upto, self.seq, st))
                    break

    def drop(self, floor):
        while self.pend and self.pend[0][0] < floor:
            heapq.heappop(self.pend)[2].gone = True
        if len(self.items) > 64:
            live = [st for st in self.items if not st.gone]
            if len(live) != len(self.items):
                self.items = live

    def near(self, lo, hi):
        return [st for st in self.items
                if not st.gone and st.hi >= lo and st.lo <= hi]
