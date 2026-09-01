from seg import rec


class Plan:
    def __init__(self, core):
        self.core = core

    def key(self, cur, pts):
        left = list(pts)
        while left:
            r = cur.next()
            if r is None:
                return
            hit = [a for a in left if a >= r.s]
            if not hit:
                continue
            for a in hit:
                left.remove(a)
            self.core.emit(r.k, r.s, r.t, r.v)
