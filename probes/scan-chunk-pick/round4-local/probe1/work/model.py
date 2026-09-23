"""Slow literal model of the brief. Recomputes everything from scratch."""
import sys
import os
from itertools import combinations, product

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from scn import parse  # noqa: E402

CMP = ("ge", "le", "eq", "ne")


def sat(kind, v0, x):
    if x is None:
        return kind == "nu"
    if kind == "nu":
        return False
    if kind == "nn":
        return True
    if kind == "ge":
        return x >= v0
    if kind == "le":
        return x <= v0
    if kind == "eq":
        return x == v0
    return x != v0


class Model:
    def __init__(self, seg):
        self.seg = seg
        self.read = set()
        self.dknown = set()
        self.out = []
        self._where = {}
        for c in range(seg.k):
            for ch in seg.cols[c]:
                for pg in ch.pages:
                    for r in range(pg.start, pg.start + pg.n):
                        self._where[(c, r)] = (ch, pg)
        self._alive = None

    # --- static facts -------------------------------------------------
    def bounds(self, pg):
        if pg.nulls == pg.n:
            return None
        if pg.exact:
            return (pg.mn, pg.mx)
        g = self.seg.g
        return (pg.mn - (g - 1), pg.mx + (g - 1))

    def written(self, ch, pg):
        if pg.form == "v":
            return list(pg.toks)
        return [None if t is None else ch.dic[t] for t in pg.toks]

    def page_of(self, c, r):
        return self._where[(c, r)]

    def has_up(self, c, r):
        return r in self.seg.up[c]

    def value(self, c, r):
        if self.has_up(c, r):
            return self.seg.up[c][r]
        ch, pg = self.page_of(c, r)
        return self.written(ch, pg)[r - pg.start]

    # --- knowledge ----------------------------------------------------
    def header_says(self, cd, pg):
        """'fail' / 'pass' / None from what the header proves."""
        b = self.bounds(pg)
        u, n = pg.nulls, pg.n
        poss_sat = []  # for each class of possible value: can it satisfy? must it?
        # null class
        if u > 0:
            s = sat(cd.kind, cd.v, None)
            poss_sat.append((s, s))
        if u < n:
            lo, hi = b
            k, v = cd.kind, cd.v
            if k == "nu":
                some, every = False, False
            elif k == "nn":
                some, every = True, True
            elif k == "ge":
                some, every = hi >= v, lo >= v
            elif k == "le":
                some, every = lo <= v, hi <= v
            elif k == "eq":
                some, every = lo <= v <= hi, lo == hi == v
            else:
                some, every = not (lo == hi == v), (v < lo or v > hi)
            poss_sat.append((some, every))
        if not any(s for s, e in poss_sat):
            return "fail"
        if all(e for s, e in poss_sat):
            return "pass"
        return None

    def dict_says(self, cd, ch, pg):
        if cd.kind not in CMP or pg.form != "i" or (ch.c, ch.j) not in self.dknown:
            return None
        good = [e for e in ch.dic if sat(cd.kind, cd.v, e)]
        if not good:
            return "fail"
        if len(good) == len(ch.dic) and pg.nulls == 0:
            return "pass"
        return None

    def known(self, cd, r):
        """None if unsettled, else True (satisfies) / False (fails)."""
        c = cd.c
        if self.has_up(c, r):
            return sat(cd.kind, cd.v, self.seg.up[c][r])
        ch, pg = self.page_of(c, r)
        if (c, ch.j, pg.p) in self.read:
            return sat(cd.kind, cd.v, self.written(ch, pg)[r - pg.start])
        h = self.header_says(cd, pg)
        if h is None:
            h = self.dict_says(cd, ch, pg)
        if h is None:
            return None
        return h == "pass"

    def refresh(self, q):
        self._alive = None
        self._alive = {r for r in range(self.seg.n) if self.alive(q, r)}

    def alive(self, q, r):
        if self._alive is not None:
            return r in self._alive
        if r in self.seg.gone:
            return False
        for cd in q.conds:
            if self.known(cd, r) is False:
                return False
        return True

    # --- counts -------------------------------------------------------
    def spread(self, cd, pg):
        k, v = cd.kind, cd.v
        b = self.bounds(pg)
        if k == "nu":
            return pg.nulls
        if b is None:
            return 0
        have = pg.n - pg.nulls
        if k == "nn":
            return have
        lo, hi = b
        width = hi - lo + 1
        if k == "ge":
            part = hi - v + 1
        elif k == "le":
            part = v - lo + 1
        else:
            part = 1 if lo <= v <= hi else 0
        if part <= 0:
            return have if k == "ne" else 0
        part = min(part, width)
        x = (have * part + width - 1) // width
        return have - x if k == "ne" else x

    def page_count(self, cd, ch, pg, read_at_start, read_now):
        key = (ch.c, ch.j, pg.p)
        if key in read_now:
            vals = self.written(ch, pg)
            return sum(1 for x in vals if sat(cd.kind, cd.v, x))
        return self.spread(cd, pg)

    # --- query --------------------------------------------------------
    def holds_unsettled(self, q, cd, pg):
        c = cd.c
        for r in range(pg.start, pg.start + pg.n):
            if self.alive(q, r) and not self.has_up(c, r) and self.known(cd, r) is None:
                return True
        return False

    def pending(self, q, cd, ch):
        return any(self.holds_unsettled(q, cd, pg) for pg in ch.pages)

    def run_query(self, qi, q):
        self.out.append("qry %d" % qi)
        read_at_start = set(self.read)
        while True:
            self.refresh(q)
            best = None
            for cd in q.conds:
                for ch in self.seg.cols[cd.c]:
                    if not self.pending(q, cd, ch):
                        continue
                    live = sum(1 for r in range(ch.start, ch.start + ch.n) if self.alive(q, r))
                    cnt = sum(self.page_count(cd, ch, pg, read_at_start, self.read) for pg in ch.pages)
                    key = (min(live, cnt), cd.pos, ch.j)
                    if best is None or key < best[0]:
                        best = (key, cd, ch)
            if best is None:
                break
            _, cd, ch = best
            for pg in ch.pages:
                if not self.holds_unsettled(q, cd, pg):
                    continue
                if cd.kind in CMP and pg.form == "i" and (ch.c, ch.j) not in self.dknown:
                    self.dknown.add((ch.c, ch.j))
                    self.out.append("rd %d %d" % (ch.c, ch.j))
                    self.refresh(q)
                if self.holds_unsettled(q, cd, pg):
                    assert (ch.c, ch.j, pg.p) not in self.read
                    self.read.add((ch.c, ch.j, pg.p))
                    self.out.append("dc %d %d %d" % (ch.c, ch.j, pg.p))
                    self.refresh(q)
        self.refresh(q)
        rows = [r for r in range(self.seg.n) if self.alive(q, r)]
        self._alive = None
        # every live row satisfies every condition by value
        for r in rows:
            for cd in q.conds:
                assert sat(cd.kind, cd.v, self.value(cd.c, r)), (qi, r, cd.kind)
        h = 0
        for r in rows:
            h = (h * 1000003 + r + 1) % 2305843009213693951
        self.out.append("sel %d %d" % (len(rows), h))
        for c in q.cols:
            self.report(q, c, rows)

    # --- report -------------------------------------------------------
    def supplied(self, c, pg, rows_set):
        return [r for r in range(pg.start, pg.start + pg.n) if r in rows_set and not self.has_up(c, r)]

    def chunk_determined(self, c, ch, rows_set, readset, dk):
        """Is this chunk's part of the line determined, given pages in readset
        read and the dictionary known iff dk? Enumerates null placements."""
        single_dict = ch.enc == "d" and len(ch.dic) == 1 and dk
        pages = []
        for pg in ch.pages:
            key = (c, ch.j, pg.p)
            sup = set(self.supplied(c, pg, rows_set))
            vals = self.written(ch, pg)
            if key in readset:
                kind = "read"
            elif pg.nulls == pg.n:
                kind = "null"
            else:
                b = self.bounds(pg)
                if b[0] == b[1]:
                    kind = ("single", b[0])
                elif single_dict and pg.form == "i":
                    kind = ("single", ch.dic[0])
                else:
                    kind = "general"
            pages.append((pg, kind, sup, vals))
        # placements for unknown pages (not read, not all null)
        opts = []
        for pg, kind, sup, vals in pages:
            if kind in ("read", "null"):
                opts.append([None])
            else:
                idx = list(range(pg.start, pg.start + pg.n))
                if not sup or len(sup) == pg.n:
                    # placement cannot change which non-null rows are supplied
                    opts.append([frozenset(idx[:pg.nulls])])
                else:
                    # rows inside the supplied set are interchangeable, and so
                    # are rows outside it: only how many nulls fall in it matters
                    ins = sorted(sup)
                    outs = [r for r in idx if r not in sup]
                    u = pg.nulls
                    ch_ = []
                    for kk in range(max(0, u - len(outs)), min(u, len(ins)) + 1):
                        ch_.append(frozenset(ins[:kk] + outs[:u - kk]))
                    opts.append(ch_)
        results = set()
        for combo in product(*opts):
            nn = 0
            fixed_sup = 0
            fixed_written = 0
            free = []
            free_sup = []
            for (pg, kind, sup, vals), nulls in zip(pages, combo):
                if kind == "read":
                    for i, x in enumerate(vals):
                        r = pg.start + i
                        if x is not None:
                            fixed_written += x
                            if r in sup:
                                nn += 1
                                fixed_sup += x
                elif kind == "null":
                    pass
                else:
                    for r in range(pg.start, pg.start + pg.n):
                        if r in nulls:
                            continue
                        if r in sup:
                            nn += 1
                        if kind == "general":
                            free.append(r)
                            if r in sup:
                                free_sup.append(r)
                        else:
                            L = kind[1]
                            fixed_written += L
                            if r in sup:
                                fixed_sup += L
            if not free or not free_sup:
                tot = fixed_sup
            elif len(free_sup) == len(free):
                tot = fixed_sup + (ch.sum - fixed_written)
            else:
                return False
            results.add((nn, tot))
            if len(results) > 1:
                return False
        return True

    def decide(self, c, ch, rows_set, dk):
        """Sequential literal rule; also checks the global-hypothetical form."""
        cand = []
        for pg in ch.pages:
            if (c, ch.j, pg.p) in self.read:
                continue
            if self.supplied(c, pg, rows_set):
                cand.append(pg)
        decided_read = []
        skipped = []
        for i, pg in enumerate(cand):
            later = cand[i + 1:]
            hyp = set(self.read) | {(c, ch.j, p.p) for p in decided_read} | {(c, ch.j, p.p) for p in later}
            if not self.chunk_determined(c, ch, rows_set, hyp, dk):
                decided_read.append(pg)
            else:
                skipped.append(pg)
        # global form: all other candidates read
        glob = []
        for pg in cand:
            hyp = set(self.read) | {(c, ch.j, p.p) for p in cand if p is not pg}
            if not self.chunk_determined(c, ch, rows_set, hyp, dk):
                glob.append(pg)
        assert [p.p for p in glob] == [p.p for p in decided_read], (c, ch.j, [p.p for p in glob], [p.p for p in decided_read])
        return decided_read

    def report(self, q, c, rows):
        rows_set = set(rows)
        for ch in self.seg.cols[c]:
            any_sup = any(self.supplied(c, pg, rows_set) for pg in ch.pages)
            if not any_sup:
                continue
            dk = (c, ch.j) in self.dknown
            need = self.decide(c, ch, rows_set, dk)
            if (ch.enc == "d" and len(ch.dic) == 1 and not dk
                    and any(pg.form == "i" and self.supplied(c, pg, rows_set) for pg in ch.pages)):
                alt = self.decide(c, ch, rows_set, True)
                if len(alt) < len(need):
                    self.dknown.add((c, ch.j))
                    self.out.append("rd %d %d" % (c, ch.j))
                    need = alt
            for pg in need:
                self.read.add((c, ch.j, pg.p))
                self.out.append("dc %d %d %d" % (c, ch.j, pg.p))
            assert self.chunk_determined(c, ch, rows_set, self.read, (c, ch.j) in self.dknown)
        nn = 0
        tot = 0
        for r in rows:
            v = self.value(c, r)
            if v is not None:
                nn += 1
                tot += v
        self.out.append("prj %d %d %d" % (c, nn, tot))


def run(text):
    seg, queries = parse.load(text)
    m = Model(seg)
    for i, q in enumerate(queries):
        m.run_query(i, q)
    return m.out


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as fh:
        sys.stdout.write("\n".join(run(fh.read())) + "\n")
