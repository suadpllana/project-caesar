"""model.py's reading with incremental live counts and chunk counts, and a
plain linear scan over every pair per step (no heap).  Slow but feasible on
the shipped wide file; used only to cross-check the app there."""
import sys

import model

CMP = model.CMP
sat = model.sat


def run(text):
    G, N, K, cols, ups, gone, queries = model.parse(text)
    read = set()
    seen = set()
    out = []

    def bounds(pg):
        if pg.mn is None:
            return None
        if pg.e:
            return pg.mn, pg.mx
        return pg.mn - (G - 1), pg.mx + (G - 1)

    def estimate(pg, kind, v):
        have = pg.n - pg.u
        if kind == "nu":
            return pg.u
        b = bounds(pg)
        if b is None:
            return 0
        if kind == "nn":
            return have
        lo, hi = b
        width = hi - lo + 1
        if kind == "ge":
            part = hi - v + 1
        elif kind == "le":
            part = v - lo + 1
        else:
            part = 1 if lo <= v <= hi else 0
        if part <= 0:
            return have if kind == "ne" else 0
        part = min(part, width)
        x = -(-(have * part) // width)
        return have - x if kind == "ne" else x

    def header(pg, kind, v):
        n, u = pg.n, pg.u
        if kind == "nu":
            return "hold" if u == n else ("fail" if u == 0 else None)
        if kind == "nn":
            return "hold" if u == 0 else ("fail" if u == n else None)
        b = bounds(pg)
        if b is None or u == n:
            return "fail"
        lo, hi = b
        ok = [x for x in (lo, hi) if sat(kind, x, v)]
        # endpoints plus v itself decide an interval question for these kinds
        if kind == "ge":
            none = hi < v
            allv = lo >= v
        elif kind == "le":
            none = lo > v
            allv = hi <= v
        elif kind == "eq":
            none = not (lo <= v <= hi)
            allv = lo == hi == v
        else:
            none = lo == hi == v
            allv = not (lo <= v <= hi)
        if none:
            return "fail"
        if allv and u == 0:
            return "hold"
        return None

    def chunk_count(c, j, kind, v):
        t = 0
        for p, pg in enumerate(cols[c][j].pages):
            if (c, j, p) in read:
                t += sum(1 for x in pg.vals if sat(kind, x, v))
            else:
                t += estimate(pg, kind, v)
        return t

    def chunk_of(c):
        m = [0] * N
        for j, ch in enumerate(cols[c]):
            for r in range(ch.start, ch.start + ch.n):
                m[r] = j
        return m

    cmap = [chunk_of(c) for c in range(K)]

    for qi, q in enumerate(queries):
        out.append("qry %d" % qi)
        alive = [r not in gone for r in range(N)]
        conds = q.conds
        ccols = sorted(set(c for _, c, _ in conds))
        live = {}
        for c in ccols:
            live[c] = [sum(1 for r in range(ch.start, ch.start + ch.n) if alive[r])
                       for ch in cols[c]]
        cnt = [[chunk_count(c, j, kind, v) for j in range(len(cols[c]))]
               for kind, c, v in conds]
        applied = [[False] * len(cols[c]) for _, c, _ in conds]
        while True:
            best = None
            for pos, (kind, c, v) in enumerate(conds):
                lv = live[c]
                cp = cnt[pos]
                ap = applied[pos]
                for j in range(len(lv)):
                    if ap[j] or lv[j] == 0:
                        continue
                    k = lv[j] if lv[j] < cp[j] else cp[j]
                    if best is None or k < best[0]:
                        best = (k, pos, j)
            if best is None:
                break
            _, pos, j = best
            applied[pos][j] = True
            kind, c, v = conds[pos]
            ch = cols[c][j]
            up = ups[c]
            fail = []
            reread = False
            for r in range(ch.start, ch.start + ch.n):
                if alive[r] and r in up and not sat(kind, up[r], v):
                    fail.append(r)
            for p, pg in enumerate(ch.pages):
                mine = [r for r in range(pg.start, pg.start + pg.n)
                        if alive[r] and r not in up]
                if not mine:
                    continue
                h = header(pg, kind, v)
                if h is None and (c, j, p) not in read and kind in CMP and pg.form == "i":
                    if (c, j) not in seen:
                        seen.add((c, j))
                        out.append("rd %d %d" % (c, j))
                    good = [e for e in ch.dic if sat(kind, e, v)]
                    if not good:
                        h = "fail"
                    elif len(good) == len(ch.dic) and pg.u == 0:
                        h = "hold"
                if h is None:
                    if (c, j, p) not in read:
                        read.add((c, j, p))
                        out.append("dc %d %d %d" % (c, j, p))
                        reread = True
                    for r in mine:
                        if not sat(kind, pg.vals[r - pg.start], v):
                            fail.append(r)
                elif h == "fail":
                    fail.extend(mine)
            if reread:
                for pos2, (k2, c2, v2) in enumerate(conds):
                    if c2 == c:
                        cnt[pos2][j] = chunk_count(c, j, k2, v2)
            for r in fail:
                alive[r] = False
                for c2 in ccols:
                    live[c2][cmap[c2][r]] -= 1
        rows = [r for r in range(N) if alive[r]]
        h = 0
        for r in rows:
            h = (h * 1000003 + r + 1) % model.MOD
        out.append("sel %d %d" % (len(rows), h))
        for c in q.cols:
            nn = 0
            tot = 0
            up = ups[c]
            for r in rows:
                if r in up and up[r] is not None:
                    nn += 1
                    tot += up[r]
            for j, ch in enumerate(cols[c]):
                for p, pg in enumerate(ch.pages):
                    mine = [r for r in range(pg.start, pg.start + pg.n)
                            if alive[r] and r not in up]
                    if not mine:
                        continue
                    k = len(mine)
                    b = bounds(pg)
                    if (c, j, p) not in read:
                        if pg.u == pg.n:
                            continue
                        if pg.u == 0 and b[0] == b[1]:
                            nn += k
                            tot += k * b[0]
                            continue
                        if k == pg.n:
                            nn += pg.n - pg.u
                            tot += pg.s
                            continue
                        if pg.form == "i" and pg.u == 0 and len(ch.dic) == 1:
                            if (c, j) not in seen:
                                seen.add((c, j))
                                out.append("rd %d %d" % (c, j))
                            nn += k
                            tot += k * ch.dic[0]
                            continue
                        read.add((c, j, p))
                        out.append("dc %d %d %d" % (c, j, p))
                    for r in mine:
                        x = pg.vals[r - pg.start]
                        if x is not None:
                            nn += 1
                            tot += x
            out.append("prj %d %d %d" % (c, nn, tot))
    return out


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as fh:
        sys.stdout.write("\n".join(run(fh.read())) + "\n")
