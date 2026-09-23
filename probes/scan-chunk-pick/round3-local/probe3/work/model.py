"""Slow, literal reading of the brief. Own parser, no shared code with app/scn.

Used only as an oracle for random differential testing of the fast version.
"""
import sys

MOD = 2305843009213693951
STATS = {}


def tick(k):
    STATS[k] = STATS.get(k, 0) + 1
CMP = ("ge", "le", "eq", "ne")


class P:
    pass


def parse(text):
    G = N = K = 0
    cols = ups = None
    gone = set()
    queries = []
    cur = None
    chk = None
    ends = None
    for line in text.split("\n"):
        f = line.split()
        if not f:
            continue
        t = f[0]
        if t == "seg":
            G, N, K = int(f[1]), int(f[2]), int(f[3])
            cols = [[] for _ in range(K)]
            ups = [{} for _ in range(K)]
            ends = [0] * K
        elif t == "ch":
            c = int(f[1])
            chk = P()
            chk.c = c
            chk.enc = f[2]
            if f[2] == "d":
                m = int(f[3])
                chk.dic = [int(x) for x in f[4:4 + m]]
            else:
                chk.dic = None
            chk.pages = []
            chk.start = ends[c]
            chk.n = 0
            cols[c].append(chk)
        elif t == "pg":
            pg = P()
            pg.n = int(f[1])
            pg.u = int(f[2])
            pg.mn = None if f[3] == "-" else int(f[3])
            pg.mx = None if f[4] == "-" else int(f[4])
            pg.e = f[5] == "e"
            pg.s = int(f[6])
            pg.form = f[7]
            raw = f[8:8 + pg.n]
            vals = []
            for tk in raw:
                if tk == "-":
                    vals.append(None)
                elif pg.form == "i":
                    vals.append(chk.dic[int(tk)])
                else:
                    vals.append(int(tk))
            pg.vals = vals
            pg.start = ends[chk.c]
            ends[chk.c] += pg.n
            chk.n += pg.n
            chk.pages.append(pg)
        elif t == "up":
            ups[int(f[1])][int(f[2])] = None if f[3] == "-" else int(f[3])
        elif t == "del":
            gone.add(int(f[1]))
        elif t == "qry":
            cur = P()
            cur.conds = []
            cur.cols = []
        elif t == "prd":
            kind = f[1]
            c = int(f[2])
            v = int(f[3]) if len(f) > 3 else None
            cur.conds.append((kind, c, v))
        elif t == "prj":
            cur.cols.extend(int(x) for x in f[1:])
        elif t == "end":
            queries.append(cur)
            cur = None
    return G, N, K, cols, ups, gone, queries


def sat(kind, x, v):
    if x is None:
        return kind == "nu"
    if kind == "nu":
        return False
    if kind == "nn":
        return True
    if kind == "ge":
        return x >= v
    if kind == "le":
        return x <= v
    if kind == "eq":
        return x == v
    return x != v


def run(text):
    G, N, K, cols, ups, gone, queries = parse(text)
    read = set()
    seen = set()
    out = []

    def bounds(pg):
        if pg.mn is None:
            return None
        if pg.e:
            return pg.mn, pg.mx
        return pg.mn - (G - 1), pg.mx + (G - 1)

    def n_sat_in(kind, v, lo, hi):
        # how many integers of [lo, hi] satisfy the comparison
        if kind == "ge":
            return max(0, hi - max(lo, v) + 1)
        if kind == "le":
            return max(0, min(hi, v) - lo + 1)
        inside = 1 if lo <= v <= hi else 0
        if kind == "eq":
            return inside
        return (hi - lo + 1) - inside

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
        k = n_sat_in(kind, v, lo, hi)
        if k == 0:
            return "fail"
        if k == hi - lo + 1 and u == 0:
            return "hold"
        return None

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
        num = have * part
        x = num // width + (1 if num % width else 0)
        return have - x if kind == "ne" else x

    def exact(pg, kind, v):
        return sum(1 for x in pg.vals if sat(kind, x, v))

    def consult(c, j):
        if (c, j) not in seen:
            seen.add((c, j))
            out.append("rd %d %d" % (c, j))

    def doread(c, j, p):
        if (c, j, p) not in read:
            read.add((c, j, p))
            out.append("dc %d %d %d" % (c, j, p))

    for qi, q in enumerate(queries):
        out.append("qry %d" % qi)
        alive = [r not in gone for r in range(N)]
        applied = set()
        while True:
            best = None
            for pos, (kind, c, v) in enumerate(q.conds):
                for j, ch in enumerate(cols[c]):
                    if (pos, j) in applied:
                        continue
                    live = sum(1 for r in range(ch.start, ch.start + ch.n) if alive[r])
                    if live == 0:
                        continue
                    cnt = 0
                    for p, pg in enumerate(ch.pages):
                        if (c, j, p) in read:
                            cnt += exact(pg, kind, v)
                        else:
                            cnt += estimate(pg, kind, v)
                    key = (min(live, cnt), pos, j)
                    if best is None or key < best:
                        best = key
            if best is None:
                break
            _, pos, j = best
            applied.add((pos, j))
            kind, c, v = q.conds[pos]
            ch = cols[c][j]
            up = ups[c]
            fail = []
            for r in range(ch.start, ch.start + ch.n):
                if alive[r] and r in up and not sat(kind, up[r], v):
                    fail.append(r)
            for p, pg in enumerate(ch.pages):
                mine = [r for r in range(pg.start, pg.start + pg.n)
                        if alive[r] and r not in up]
                if not mine:
                    continue
                h = header(pg, kind, v)
                tick("apply_hdr_" + str(h))
                if h is None and (c, j, p) in read:
                    tick("apply_readmade")
                if h is None and (c, j, p) not in read and kind in CMP and pg.form == "i":
                    consult(c, j)
                    good = [e for e in ch.dic if sat(kind, e, v)]
                    if not good:
                        h = "fail"
                    elif len(good) == len(ch.dic) and pg.u == 0:
                        h = "hold"
                    tick("apply_dict_" + str(h))
                if h is None:
                    if (c, j, p) not in read:
                        tick("apply_read")
                    doread(c, j, p)
                    for r in mine:
                        if not sat(kind, pg.vals[r - pg.start], v):
                            fail.append(r)
                elif h == "fail":
                    fail.extend(mine)
            for r in fail:
                alive[r] = False
        rows = [r for r in range(N) if alive[r]]
        h = 0
        for r in rows:
            h = (h * 1000003 + r + 1) % MOD
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
                    if (c, j, p) in read:
                        tick("proj_readmade")
                    elif pg.u == pg.n:
                        tick("proj_allnull")
                        continue
                    elif pg.u == 0 and b[0] == b[1]:
                        tick("proj_onevalue" + ("_w" if not pg.e else ""))
                        nn += k
                        tot += k * b[0]
                        continue
                    elif k == pg.n:
                        tick("proj_everyrow")
                        nn += pg.n - pg.u
                        tot += pg.s
                        continue
                    elif pg.form == "i" and pg.u == 0 and len(ch.dic) == 1:
                        tick("proj_dict" + ("_new" if (c, j) not in seen else "_known"))
                        consult(c, j)
                        nn += k
                        tot += k * ch.dic[0]
                        continue
                    else:
                        tick("proj_read")
                        doread(c, j, p)
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
