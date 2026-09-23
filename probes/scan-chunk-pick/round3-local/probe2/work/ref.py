"""Slow, literal reading of the brief. Used only to cross-check the fast scanner."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "orig"))

from scn import parse  # noqa: E402  (fixed module, same as the shipped one)

MOD = 2305843009213693951


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


def written(ch, pg):
    out = []
    for t in pg.toks:
        if t is None:
            out.append(None)
        elif pg.form == "i":
            out.append(ch.dic[t])
        else:
            out.append(t)
    return out


def run(text):
    seg, queries = parse.load(text)
    G = seg.g
    lines = []
    read = {}      # (c, j, p) -> written values
    dicts = set()  # (c, j)

    def bounds(pg):
        if pg.nulls == pg.n:
            return None
        if pg.exact:
            return (pg.mn, pg.mx)
        return (pg.mn - (G - 1), pg.mx + (G - 1))

    def header_settles(pg, kind, v):
        # facts: u nulls; every other value in bounds
        u = pg.nulls
        b = bounds(pg)
        rows_null_sat = sat(kind, None, v)
        if b is None:
            # all rows null
            return True if rows_null_sat else False
        lo, hi = b
        # does every value in [lo, hi] satisfy / fail?  (integers)
        if kind == "nu":
            all_sat, all_fail = False, True
        elif kind == "nn":
            all_sat, all_fail = True, False
        elif kind == "ge":
            all_sat, all_fail = lo >= v, hi < v
        elif kind == "le":
            all_sat, all_fail = hi <= v, lo > v
        elif kind == "eq":
            all_sat, all_fail = (lo == hi == v), (v < lo or v > hi)
        else:
            all_sat, all_fail = (v < lo or v > hi), (lo == hi == v)
        holds = all_sat and (u == 0 or rows_null_sat)
        fails = all_fail and (u == 0 or not rows_null_sat)
        if holds:
            return True
        if fails:
            return False
        return None

    def dict_settles(ch, pg, kind, v):
        good = [e for e in ch.dic if sat(kind, e, v)]
        if not good:
            return False
        if len(good) == len(ch.dic) and pg.nulls == 0:
            return True
        return None

    def spread(pg, kind, v):
        u = pg.nulls
        have = pg.n - u
        if kind == "nu":
            return u
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
        k = (have * part + width - 1) // width
        return have - k if kind == "ne" else k

    def exact(ch, pg, kind, v):
        return sum(1 for x in read[(ch.c, ch.j, pg.p)] if sat(kind, x, v))

    def do_read(ch, pg):
        key = (ch.c, ch.j, pg.p)
        if key not in read:
            lines.append("dc %d %d %d" % key)
            read[key] = written(ch, pg)
        return read[key]

    def consult(ch):
        key = (ch.c, ch.j)
        if key not in dicts:
            dicts.add(key)
            lines.append("rd %d %d" % key)

    for qi, q in enumerate(queries):
        lines.append("qry %d" % qi)
        alive = set(range(seg.n)) - seg.gone
        applied = set()
        while True:
            best = None
            for cd in q.conds:
                for ch in seg.cols[cd.c]:
                    if (cd.pos, ch.j) in applied:
                        continue
                    lv = sum(1 for r in range(ch.start, ch.start + ch.n) if r in alive)
                    if lv == 0:
                        continue
                    cnt = 0
                    for pg in ch.pages:
                        if (ch.c, ch.j, pg.p) in read:
                            cnt += exact(ch, pg, cd.kind, cd.v)
                        else:
                            cnt += spread(pg, cd.kind, cd.v)
                    key = (min(lv, cnt), cd.pos, ch.j)
                    if best is None or key < best[0]:
                        best = (key, cd, ch)
            if best is None:
                break
            _, cd, ch = best
            applied.add((cd.pos, ch.j))
            c = cd.c
            up = seg.up[c]
            dead = set()
            for r in range(ch.start, ch.start + ch.n):
                if r in alive and r in up and not sat(cd.kind, up[r], cd.v):
                    dead.add(r)
            for pg in ch.pages:
                rows = [r for r in range(pg.start, pg.start + pg.n) if r in alive and r not in up]
                if not rows:
                    continue
                verdict = header_settles(pg, cd.kind, cd.v)
                if verdict is None and (c, ch.j, pg.p) in read:
                    vals = read[(c, ch.j, pg.p)]
                    for r in rows:
                        if not sat(cd.kind, vals[r - pg.start], cd.v):
                            dead.add(r)
                    continue
                if verdict is None and cd.kind not in ("nn", "nu") and pg.form == "i":
                    consult(ch)
                    verdict = dict_settles(ch, pg, cd.kind, cd.v)
                if verdict is None:
                    vals = do_read(ch, pg)
                    for r in rows:
                        if not sat(cd.kind, vals[r - pg.start], cd.v):
                            dead.add(r)
                    continue
                if verdict is False:
                    dead.update(rows)
            alive -= dead
        rows = sorted(alive)
        h = 0
        for r in rows:
            h = (h * 1000003 + r + 1) % MOD
        lines.append("sel %d %d" % (len(rows), h))
        for c in q.cols:
            up = seg.up[c]
            nn = 0
            tot = 0
            for ch in seg.cols[c]:
                for pg in ch.pages:
                    rs = [r for r in range(pg.start, pg.start + pg.n) if r in alive and r not in up]
                    if not rs:
                        continue
                    key = (c, ch.j, pg.p)
                    if key in read:
                        for r in rs:
                            x = read[key][r - pg.start]
                            if x is not None:
                                nn += 1
                                tot += x
                        continue
                    b = bounds(pg)
                    if pg.nulls == pg.n:
                        continue
                    if pg.nulls == 0 and b[0] == b[1]:
                        nn += len(rs)
                        tot += len(rs) * b[0]
                        continue
                    if len(rs) == pg.n:
                        nn += pg.n - pg.nulls
                        tot += pg.sum
                        continue
                    if pg.form == "i" and pg.nulls == 0 and len(ch.dic) == 1:
                        consult(ch)
                        nn += len(rs)
                        tot += len(rs) * ch.dic[0]
                        continue
                    vals = do_read(ch, pg)
                    for r in rs:
                        x = vals[r - pg.start]
                        if x is not None:
                            nn += 1
                            tot += x
            for r in sorted(alive):
                if r in up and up[r] is not None:
                    nn += 1
                    tot += up[r]
            lines.append("prj %d %d %d" % (c, nn, tot))
    return lines


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as fh:
        sys.stdout.write("\n".join(run(fh.read())) + "\n")
