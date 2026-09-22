# Correct variant V2: a scope tree with interval lookup instead of per-address tables.
from dbg.image import Inl


class Tree:
    def __init__(self, img):
        self.img = img
        self.kids = {}
        for i in img.inls:
            self.kids.setdefault(id(i.up), []).append(i)
        rows = sorted(img.rows, key=lambda r: r.at)
        self.rows = rows
        self.row_ats = [r.at for r in rows]

    def scopes(self, addr):
        f = self.img.fn_at(addr)
        out = [f]
        cur = f
        while True:
            nxt = None
            for k in self.kids.get(id(cur), ()):
                if k.lo <= addr <= k.hi:
                    nxt = k
                    break
            if nxt is None:
                return out
            out.append(nxt)
            cur = nxt

    def row(self, addr):
        import bisect
        f = self.img.fn_at(addr)
        i = bisect.bisect_right(self.row_ats, addr) - 1
        if i < 0 or self.rows[i].at < f.lo:
            return None
        return self.rows[i]

    def line(self, addr):
        r = self.row(addr)
        return r.line if r else 0


_trees = {}


def tree(img):
    t = _trees.get(id(img))
    if t is None or t.img is not img:
        t = _trees[id(img)] = Tree(img)
    return t


def title(s):
    return s.fn.name if isinstance(s, Inl) else s.name


def show(img, pc, stack, hid):
    t = tree(img)
    frames = []
    spots = [(pc, hid)]
    for r in reversed(stack):
        spots.append((r - 1, 0))
    for addr, h in spots:
        sc = t.scopes(addr)
        keep = len(sc) - h
        for k in reversed(range(keep)):
            if k + 1 < len(sc):
                frames.append((title(sc[k]), sc[k + 1].call))
            else:
                frames.append((title(sc[k]), t.line(addr)))
    return frames
