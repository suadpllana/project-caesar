"""Literal, slow reading of the brief. Used only to cross-check the fast code."""
import os
import sys

APP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app")
sys.path.insert(0, APP)

from scn import emit, parse  # noqa: E402

CMP = ("ge", "le", "eq", "ne")


def sat(cd, v):
    k = cd.kind
    if v is None:
        return k == "nu"
    if k == "nu":
        return False
    if k == "nn":
        return True
    if k == "ge":
        return v >= cd.v
    if k == "le":
        return v <= cd.v
    if k == "eq":
        return v == cd.v
    if k == "ne":
        return v != cd.v
    raise ValueError(k)


class Ref:
    def __init__(self, text):
        self.seg, self.queries = parse.load(text)
        seg = self.seg
        self.G = seg.g
        self.read = set()
        self.dk = set()
        self.out = []
        self.pageat = []
        for c in range(seg.k):
            m = {}
            for ch in seg.cols[c]:
                for pg in ch.pages:
                    for r in range(pg.start, pg.start + pg.n):
                        m[r] = pg
            self.pageat.append(m)

    # ---- header -------------------------------------------------------
    def bounds(self, pg):
        if pg.mn is None:
            return None
        if pg.exact:
            return pg.mn, pg.mx
        return pg.mn - (self.G - 1), pg.mx + (self.G - 1)

    def hdr(self, pg, cd):
        """True: holds for all rows, False: fails for all rows, None: open."""
        b = self.bounds(pg)
        n, u = pg.n, pg.nulls
        if b is None:
            return cd.kind == "nu"
        lo, hi = b
        if cd.kind == "nu":
            return True if u == n else (False if u == 0 else None)
        if cd.kind == "nn":
            return True if u == 0 else (False if u == n else None)
        pts = [x for x in (lo, hi, cd.v) if lo <= x <= hi]
        anys = any(sat(cd, x) for x in pts)
        alls = all(sat(cd, x) for x in pts)
        if not anys:
            return False
        if alls and u == 0:
            return True
        return None

    def dct(self, ch, pg, cd):
        good = [e for e in ch.dic if sat(cd, e)]
        if not good:
            return False
        if len(good) == len(ch.dic) and pg.nulls == 0:
            return True
        return None

    def written(self, c, r):
        pg = self.pageat[c][r]
        t = pg.toks[r - pg.start]
        if t is None:
            return None
        if pg.form == "i":
            return self.seg.cols[c][pg.j].dic[t]
        return t

    def value(self, c, r):
        up = self.seg.up[c]
        if r in up:
            return up[r]
        return self.written(c, r)

    def status(self, r, cd):
        c = cd.c
        up = self.seg.up[c]
        if r in up:
            return sat(cd, up[r])
        pg = self.pageat[c][r]
        if (c, pg.j, pg.p) in self.read:
            return sat(cd, self.written(c, r))
        h = self.hdr(pg, cd)
        if h is not None:
            return h
        ch = self.seg.cols[c][pg.j]
        if pg.form == "i" and cd.kind in CMP and (c, pg.j) in self.dk:
            return self.dct(ch, pg, cd)
        return None

    def pagecount(self, pg, cd):
        c = pg.c
        ch = self.seg.cols[c][pg.j]
        if (c, pg.j, pg.p) in self.read:
            t = 0
            for i in range(pg.n):
                tok = pg.toks[i]
                v = None if tok is None else (ch.dic[tok] if pg.form == "i" else tok)
                if sat(cd, v):
                    t += 1
            return t
        b = self.bounds(pg)
        k = cd.kind
        if k == "nu":
            return pg.nulls
        if b is None:
            return 0
        have = pg.n - pg.nulls
        if k == "nn":
            return have
        lo, hi = b
        width = hi - lo + 1
        v = cd.v
        if k == "ge":
            part = hi - v + 1
        elif k == "le":
            part = v - lo + 1
        else:
            part = 1 if lo <= v <= hi else 0
        if part <= 0:
            return have if k == "ne" else 0
        part = min(part, width)
        x = -((-have * part) // width)
        return have - x if k == "ne" else x

    # ---- query --------------------------------------------------------
    def run(self):
        seg = self.seg
        for qi, q in enumerate(self.queries):
            self.out.append("qry %d" % qi)
            self.alive = set(range(seg.n)) - seg.gone
            self.q = q
            self.sweep()
            while True:
                best = None
                for cd in q.conds:
                    for ch in seg.cols[cd.c]:
                        if not self.pending(cd, ch):
                            continue
                        live = sum(1 for r in range(ch.start, ch.start + ch.n) if r in self.alive)
                        cnt = sum(self.pagecount(pg, cd) for pg in ch.pages)
                        key = (min(live, cnt), cd.pos, ch.j)
                        if best is None or key < best[0]:
                            best = (key, cd, ch)
                if best is None:
                    break
                _, cd, ch = best
                self.apply(cd, ch)
            rows = sorted(self.alive)
            self.out.append("sel %d %d" % (len(rows), emit.digest(rows)))
            for c in q.cols:
                self.report(c)
        return self.out

    def sweep(self):
        for r in list(self.alive):
            for cd in self.q.conds:
                if self.status(r, cd) is False:
                    self.alive.discard(r)
                    break

    def holds_open(self, pg, cd):
        up = self.seg.up[cd.c]
        for r in range(pg.start, pg.start + pg.n):
            if r in self.alive and r not in up and self.status(r, cd) is None:
                return True
        return False

    def pending(self, cd, ch):
        return any(self.holds_open(pg, cd) for pg in ch.pages)

    def apply(self, cd, ch):
        c = cd.c
        for pg in ch.pages:
            if not self.holds_open(pg, cd):
                continue
            if cd.kind in CMP and pg.form == "i" and (c, ch.j) not in self.dk:
                self.out.append("rd %d %d" % (c, ch.j))
                self.dk.add((c, ch.j))
                self.sweep()
            if self.holds_open(pg, cd):
                self.out.append("dc %d %d %d" % (c, ch.j, pg.p))
                self.read.add((c, ch.j, pg.p))
                self.sweep()

    # ---- report -------------------------------------------------------
    def supplied(self, c, pg):
        up = self.seg.up[c]
        return [r for r in range(pg.start, pg.start + pg.n) if r in self.alive and r not in up]

    def determined(self, c, known, dk):
        """Can the prj line of column c be worked out from `known` pages and `dk` dictionaries?"""
        for ch in self.seg.cols[c]:
            unknown = []
            for pg in ch.pages:
                if (c, ch.j, pg.p) in known:
                    continue
                S = self.supplied(c, pg)
                full = len(S) == pg.n
                if S and not (pg.nulls == 0 or pg.nulls == pg.n or full):
                    return False
                b = self.bounds(pg)
                const = (b is not None and b[0] == b[1]) or (
                    pg.form == "i" and len(ch.dic) == 1 and (c, ch.j) in dk)
                if pg.nulls == pg.n or const:
                    continue
                unknown.append((S, full))
            sup = [t for t in unknown if t[0]]
            if not sup:
                continue
            if len(sup) == len(unknown) and all(t[1] for t in sup):
                continue
            return False
        return True

    def reads_of(self, c, ch, dk):
        allsup = set()
        for ch2 in self.seg.cols[c]:
            for pg in ch2.pages:
                if self.supplied(c, pg):
                    allsup.add((c, ch2.j, pg.p))
        res = []
        for pg in ch.pages:
            key = (c, ch.j, pg.p)
            if key in self.read or key not in allsup:
                continue
            known = set(self.read) | (allsup - {key})
            if not self.determined(c, known, dk):
                res.append(pg)
        return res

    def report(self, c):
        seg = self.seg
        for ch in seg.cols[c]:
            if (ch.enc == "d" and len(ch.dic) == 1 and (c, ch.j) not in self.dk and any(
                    pg.form == "i" and self.supplied(c, pg) for pg in ch.pages)):
                without = self.reads_of(c, ch, self.dk)
                with_ = self.reads_of(c, ch, self.dk | {(c, ch.j)})
                if len(with_) < len(without):
                    self.out.append("rd %d %d" % (c, ch.j))
                    self.dk.add((c, ch.j))
            for pg in self.reads_of(c, ch, self.dk):
                self.out.append("dc %d %d %d" % (c, ch.j, pg.p))
                self.read.add((c, ch.j, pg.p))
        nn = 0
        tot = 0
        for r in sorted(self.alive):
            v = self.value(c, r)
            if v is not None:
                nn += 1
                tot += v
        self.out.append("prj %d %d %d" % (c, nn, tot))


def run(text):
    return Ref(text).run()


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as fh:
        sys.stdout.write("\n".join(run(fh.read())) + "\n")
