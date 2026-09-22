"""The cached-stretch table.

A stretch records that, over the closed key range [lo, hi], `rows` is exactly the store's
content for every version from `born` to `died` inclusive; `died` is -1 while the stretch is
still current, which means it runs to the present version and keeps extending.

Two block indexes sit over it. `opens` is what a commit walks and holds only stretches that
are still current, so the work a commit does is bounded by the stretches that actually cover
the written key rather than by the size of the table; a stretch leaves that index the first
time a scan meets it after it was closed. `alls` is what a read walks and holds every
retained stretch, closed ones included, because a read aimed at an older version is answered
from exactly those. A stretch wider than one block is listed in each block it touches, so both
scans stamp what they have already seen with the query number rather than paying for a set.

Retention is a heap of closed stretches ordered by the last version each was correct at, so
dropping what has fallen past the horizon costs nothing on the commits where nothing has.
"""

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
    __slots__ = ("opens", "alls", "stamp", "pend", "seq")

    def __init__(self):
        self.opens = {}
        self.alls = {}
        self.stamp = 0
        self.pend = []
        self.seq = 0

    def add(self, lo, hi, rows, born):
        st = Stretch(lo, hi, rows, born)
        for b in range(lo // BLOCK, hi // BLOCK + 1):
            box = self.opens.get(b)
            if box is None:
                box = self.opens[b] = []
            box.append(st)
            box = self.alls.get(b)
            if box is None:
                box = self.alls[b] = []
            box.append(st)
        return st

    def close(self, keys, upto):
        for k in keys:
            b = k // BLOCK
            box = self.opens.get(b)
            if not box:
                continue
            keep = []
            for st in box:
                if st.died >= 0 or st.gone:
                    continue
                if st.lo <= k <= st.hi:
                    st.died = upto
                    self.seq += 1
                    heapq.heappush(self.pend, (upto, self.seq, st))
                else:
                    keep.append(st)
            self.opens[b] = keep

    def drop(self, floor):
        pend = self.pend
        while pend and pend[0][0] < floor:
            heapq.heappop(pend)[2].gone = True

    def near(self, lo, hi):
        self.stamp += 1
        tag = self.stamp
        found = []
        for b in range(lo // BLOCK, hi // BLOCK + 1):
            box = self.alls.get(b)
            if not box:
                continue
            keep = []
            for st in box:
                if st.gone:
                    continue
                keep.append(st)
                if st.tag == tag:
                    continue
                st.tag = tag
                if st.hi >= lo and st.lo <= hi:
                    found.append(st)
            if len(keep) != len(box):
                self.alls[b] = keep
        return found
