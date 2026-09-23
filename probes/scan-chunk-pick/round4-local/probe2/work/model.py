"""Slow, literal model of the brief, for cross-checking. Row-level knowledge,
everything recomputed from scratch before every decision."""
import sys
sys.path.insert(0, '/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p4_2/work/orig/app')
from scn import parse, emit  # the shipped parser, untouched copy

COMP = ('ge', 'le', 'eq', 'ne')


def sat(kind, v, x):
    if x is None:
        return kind == 'nu'
    if kind == 'nu':
        return False
    if kind == 'nn':
        return True
    if kind == 'ge':
        return x >= v
    if kind == 'le':
        return x <= v
    if kind == 'eq':
        return x == v
    return x != v


def model(text):
    seg, queries = parse.load(text)
    G, N, K = seg.g, seg.n, seg.k
    out = []
    # page lookup
    where = {}  # (c, r) -> (j, p)
    written = {}  # (c, r) -> value
    for c in range(K):
        for ch in seg.cols[c]:
            for pg in ch.pages:
                for o in range(pg.n):
                    r = pg.start + o
                    where[(c, r)] = (ch.j, pg.p)
                    t = pg.toks[o]
                    if pg.form == 'i' and t is not None:
                        t = ch.dic[t]
                    written[(c, r)] = t

    def page(c, j, p):
        return seg.cols[c][j].pages[p]

    def bnds(pg):
        if pg.mn is None:
            return None
        if pg.exact:
            return (pg.mn, pg.mx)
        return (pg.mn - (G - 1), pg.mx + (G - 1))

    def hdr_says(pg, kind, v):
        # what the two facts prove about every row
        n, u = pg.n, pg.nulls
        b = bnds(pg)
        # possible values: null (if u>0), any integer in bounds (if u<n)
        can_null = u > 0
        must_null = u == n
        if kind == 'nu':
            if must_null:
                return True
            if not can_null:
                return False
            return None
        if kind == 'nn':
            if not can_null:
                return True
            if must_null:
                return False
            return None
        if must_null:
            return False
        if b is None:
            return None
        lo, hi = b
        # does some value in [lo,hi] satisfy / fail
        vals_sat = {
            'ge': hi >= v, 'le': lo <= v, 'eq': lo <= v <= hi, 'ne': not (lo == hi == v)}[kind]
        vals_fail = {
            'ge': lo < v, 'le': hi > v, 'eq': not (lo == hi == v), 'ne': lo <= v <= hi}[kind]
        if not vals_sat:
            return False  # nulls fail too
        if not vals_fail and not can_null:
            return True
        return None

    def dict_says(ch, pg, kind, v):
        good = [e for e in ch.dic if sat(kind, v, e)]
        if not good:
            return False
        if len(good) == len(ch.dic) and pg.nulls == 0:
            return True
        return None

    def spread(pg, kind, v):
        n, u = pg.n, pg.nulls
        b = bnds(pg)
        if kind == 'nu':
            return u
        if b is None:
            return 0
        nonnull = n - u
        if kind == 'nn':
            return nonnull
        lo, hi = b
        W = hi - lo + 1
        if kind == 'ge':
            P = hi - v + 1
        elif kind == 'le':
            P = v - lo + 1
        else:
            P = 1 if lo <= v <= hi else 0
        if P <= 0:
            return nonnull if kind == 'ne' else 0
        P = min(P, W)
        import math
        cnt = (nonnull * P + W - 1) // W
        return nonnull - cnt if kind == 'ne' else cnt

    readp = set()
    dknown = set()

    for qi, q in enumerate(queries):
        out.append('qry %d' % qi)
        alive = set(range(N)) - set(seg.gone)
        conds = [(cd.kind, cd.c, cd.v) for cd in q.conds]

        def status(r, kind, c, v):
            if r in seg.up[c]:
                return sat(kind, v, seg.up[c][r])
            j, p = where[(c, r)]
            if (c, j, p) in readp:
                return sat(kind, v, written[(c, r)])
            pg = page(c, j, p)
            h = hdr_says(pg, kind, v)
            if h is not None:
                return h
            if kind in COMP and pg.form == 'i' and (c, j) in dknown:
                d = dict_says(seg.cols[c][j], pg, kind, v)
                if d is not None:
                    return d
            return None

        def purge():
            for r in sorted(alive):
                for (kind, c, v) in conds:
                    if status(r, kind, c, v) is False:
                        alive.discard(r)
                        break

        def holds_such(pos, c, j, p):
            kind, _, v = conds[pos]
            pg = page(c, j, p)
            for r in range(pg.start, pg.start + pg.n):
                if r in alive and r not in seg.up[c] and status(r, kind, c, v) is None:
                    return True
            return False

        purge()
        while True:
            best = None
            for pos, (kind, c, v) in enumerate(conds):
                for ch in seg.cols[c]:
                    if not any(holds_such(pos, c, ch.j, pg.p) for pg in ch.pages):
                        continue
                    live = sum(1 for r in range(ch.start, ch.start + ch.n) if r in alive)
                    cnt = 0
                    for pg in ch.pages:
                        if (c, ch.j, pg.p) in readp:
                            cnt += sum(1 for r in range(pg.start, pg.start + pg.n) if sat(kind, v, written[(c, r)]))
                        else:
                            cnt += spread(pg, kind, v)
                    key = (min(live, cnt), pos, ch.j)
                    if best is None or key < best:
                        best = key
            if best is None:
                break
            _, pos, j = best
            kind, c, v = conds[pos]
            ch = seg.cols[c][j]
            for pg in ch.pages:
                if not holds_such(pos, c, j, pg.p):
                    continue
                if kind in COMP and pg.form == 'i' and (c, j) not in dknown:
                    dknown.add((c, j))
                    out.append('rd %d %d' % (c, j))
                    purge()
                if holds_such(pos, c, j, pg.p):
                    readp.add((c, j, pg.p))
                    out.append('dc %d %d %d' % (c, j, pg.p))
                    purge()
            # sanity: pair no longer pending
            assert not any(holds_such(pos, c, j, pg.p) for pg in ch.pages)
        rows = sorted(alive)
        out.append('sel %d %d' % (len(rows), emit.digest(rows)))
        # report
        for c in q.cols:
            for ch in seg.cols[c]:
                j = ch.j
                sup = {}
                for pg in ch.pages:
                    sup[pg.p] = [r for r in range(pg.start, pg.start + pg.n) if r in alive and r not in seg.up[c]]

                def reads(dk):
                    single = dk and ch.dic is not None and len(ch.dic) == 1

                    def const(pg):
                        b = bnds(pg)
                        if b is not None and b[0] == b[1]:
                            return True
                        return single and pg.form == 'i'

                    def sum_known(pg):
                        return (c, j, pg.p) in readp or pg.nulls == pg.n or const(pg)

                    res = []
                    for pg in ch.pages:
                        k = len(sup[pg.p])
                        if k == 0 or (c, j, pg.p) in readp:
                            continue
                        # hypothetically every other page it could read is read
                        nn_det = pg.nulls in (0, pg.n) or k == pg.n
                        if not nn_det:
                            res.append(pg.p)
                            continue
                        if pg.nulls == pg.n or const(pg):
                            continue
                        if k == pg.n:
                            others = all(sum_known(q2) or len(sup[q2.p]) > 0 for q2 in ch.pages if q2.p != pg.p)
                            if others:
                                continue
                        res.append(pg.p)
                    return res
                dk = (c, j) in dknown
                r0 = reads(dk)
                if (ch.dic is not None and len(ch.dic) == 1 and not dk
                        and any(pg.form == 'i' and sup[pg.p] for pg in ch.pages)):
                    r1 = reads(True)
                    if len(r1) < len(r0):
                        dknown.add((c, j))
                        out.append('rd %d %d' % (c, j))
                        r0 = r1
                for p in r0:
                    readp.add((c, j, p))
                    out.append('dc %d %d %d' % (c, j, p))
            nn = 0
            tot = 0
            for r in rows:
                x = seg.up[c][r] if r in seg.up[c] else written[(c, r)]
                if x is not None:
                    nn += 1
                    tot += x
            out.append('prj %d %d %d' % (c, nn, tot))
    return out


if __name__ == '__main__':
    print('\n'.join(model(open(sys.argv[1]).read())))
