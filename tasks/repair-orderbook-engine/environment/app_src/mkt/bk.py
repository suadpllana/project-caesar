import heapq
from collections import deque


class Ord:
    __slots__ = ("oid", "hand", "side", "px", "rem", "shn", "shw",
                 "tif", "trp", "live")

    def __init__(self, oid, hand, side, px, qty, shw, tif, trp):
        self.oid = oid
        self.hand = hand
        self.side = side
        self.px = px
        self.rem = qty
        self.shw = shw
        self.shn = qty if shw is None else min(shw, qty)
        self.tif = tif
        self.trp = trp
        self.live = False


class Side:
    def __init__(self, sign):
        self.sign = sign
        self.lv = {}
        self.pq = []

    def put(self, o):
        q = self.lv.get(o.px)
        if q is None:
            q = self.lv[o.px] = deque()
            heapq.heappush(self.pq, self.sign * o.px)
        q.append(o)
        o.live = True

    def top(self):
        while self.pq:
            px = self.sign * self.pq[0]
            q = self.lv.get(px)
            if q is None:
                heapq.heappop(self.pq)
                continue
            while q and not q[0].live:
                q.popleft()
            if q:
                return px
            del self.lv[px]
            heapq.heappop(self.pq)
        return None

    def front(self, px):
        q = self.lv[px]
        while q and not q[0].live:
            q.popleft()
        return q[0] if q else None

    def take(self, px):
        self.lv[px].popleft()

    def rows(self):
        out = []
        for px in sorted(self.lv, key=lambda p: self.sign * p):
            for o in self.lv[px]:
                if o.live:
                    out.append(o)
        return out


class Bk:
    def __init__(self):
        self.b = Side(-1)
        self.s = Side(1)

    def own(self, side):
        return self.b if side == "b" else self.s

    def opp(self, side):
        return self.s if side == "b" else self.b
