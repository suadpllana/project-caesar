"""A slow, literal reading of the brief, written independently of app/scn.

Only parse.py is shared (it is fixed by the task).  Everything is recomputed from
scratch at every step: the pending pairs, the live counts, the condition counts.
"""
import sys

sys.path.insert(0, __file__.rsplit("/", 2)[0] + "/app")
from scn import parse  # noqa: E402

MOD = 2305843009213693951


def sat(kind, v, x):
    if x is None:
        return kind == "nu"
    return {"nu": False, "nn": True, "ge": x >= v, "le": x <= v, "eq": x == v, "ne": x != v}[kind]


def page_values(ch, pg):
    if pg.form == "v":
        return list(pg.toks)
    return [None if t is None else ch.dic[t] for t in pg.toks]


def page_bounds(G, pg):
    if pg.mn is None:
        return None
    if pg.exact:
        return (pg.mn, pg.mx)
    return (pg.mn - (G - 1), pg.mx + (G - 1))


def header_verdict(G, pg, kind, v):
    """Brute force over every value the header allows: 'fail', 'pass' or None."""
    b = page_bounds(G, pg)
    possible = []
    if pg.nulls > 0:
        possible.append(None)
    if pg.n - pg.nulls > 0 and b is not None:
        lo, hi = b
        # Only the positions relative to v matter; sample the interval densely
        # around v and at the ends.
        cand = {lo, hi}
        for d in (-1, 0, 1):
            if lo <= v + d <= hi:
                cand.add(v + d)
        possible.extend(cand)
    outcomes = {sat(kind, v, x) for x in possible}
    if outcomes == {False}:
        return "fail"
    if outcomes == {True}:
        return "pass"
    if not outcomes:
        return "fail"
    return None


def dict_verdict(ch, pg, kind, v):
    oks = [e for e in ch.dic if sat(kind, v, e)]
    if not oks:
        return "fail"
    if len(oks) == len(ch.dic) and pg.nulls == 0:
        return "pass"
    return None


def spread(G, pg, kind, v):
    if kind == "nu":
        return pg.nulls
    b = page_bounds(G, pg)
    if b is None:
        return 0
    nonnull = pg.n - pg.nulls
    if kind == "nn":
        return nonnull
    lo, hi = b
    wb = hi - lo + 1
    if kind == "ge":
        wp = hi - v + 1
    elif kind == "le":
        wp = v - lo + 1
    else:
        wp = 1 if lo <= v <= hi else 0
    if wp <= 0:
        return nonnull if kind == "ne" else 0
    wp = min(wp, wb)
    num = nonnull * wp
    c = num // wb + (1 if num % wb else 0)
    return nonnull - c if kind == "ne" else c


def run(text):
    seg, queries = parse.load(text)
    G = seg.g
    lines = []
    read = set()       # (c, j, p)
    consulted = set()  # (c, j)

    def do_read(c, j, p):
        if (c, j, p) not in read:
            read.add((c, j, p))
            lines.append("dc %d %d %d" % (c, j, p))

    def do_consult(c, j):
        if (c, j) not in consulted:
            consulted.add((c, j))
            lines.append("rd %d %d" % (c, j))

    for qi, q in enumerate(queries):
        lines.append("qry %d" % qi)
        alive = set(range(seg.n)) - set(seg.gone)
        applied = set()

        def count_on_page(cd, ch, pg):
            if (cd.c, ch.j, pg.p) in read:
                return sum(1 for x in page_values(ch, pg) if sat(cd.kind, cd.v, x))
            return spread(G, pg, cd.kind, cd.v)

        while True:
            best = None
            for cd in q.conds:
                for ch in seg.cols[cd.c]:
                    if (cd.pos, ch.j) in applied:
                        continue
                    nlive = sum(1 for r in range(ch.start, ch.start + ch.n) if r in alive)
                    if nlive == 0:
                        continue
                    cnt = sum(count_on_page(cd, ch, pg) for pg in ch.pages)
                    k = (min(nlive, cnt), cd.pos, ch.j)
                    if best is None or k < best[0]:
                        best = (k, cd, ch)
            if best is None:
                break
            _, cd, ch = best
            applied.add((cd.pos, ch.j))
            c = cd.c
            up = seg.up[c]
            dead = set()
            for r in range(ch.start, ch.start + ch.n):
                if r in alive and r in up and not sat(cd.kind, cd.v, up[r]):
                    dead.add(r)
            for pg in ch.pages:
                mine = [r for r in range(pg.start, pg.start + pg.n) if r in alive and r not in up]
                if not mine:
                    continue
                hv = header_verdict(G, pg, cd.kind, cd.v)
                if hv == "fail":
                    dead.update(mine)
                    continue
                if hv == "pass":
                    continue
                if (c, ch.j, pg.p) not in read:
                    if cd.kind not in ("nn", "nu") and pg.form == "i":
                        do_consult(c, ch.j)
                        dv = dict_verdict(ch, pg, cd.kind, cd.v)
                        if dv == "fail":
                            dead.update(mine)
                            continue
                        if dv == "pass":
                            continue
                    do_read(c, ch.j, pg.p)
                vals = page_values(ch, pg)
                for r in mine:
                    if not sat(cd.kind, cd.v, vals[r - pg.start]):
                        dead.add(r)
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
                    mine = [r for r in range(pg.start, pg.start + pg.n) if r in alive and r not in up]
                    if not mine:
                        continue
                    b = page_bounds(G, pg)
                    if (c, ch.j, pg.p) in read:
                        vals = page_values(ch, pg)
                        xs = [vals[r - pg.start] for r in mine]
                    elif pg.nulls == pg.n:
                        xs = [None] * len(mine)
                    elif pg.nulls == 0 and b is not None and b[0] == b[1]:
                        xs = [b[0]] * len(mine)
                    elif len(mine) == pg.n:
                        nn += pg.n - pg.nulls
                        tot += pg.sum
                        continue
                    elif pg.form == "i" and pg.nulls == 0 and len(ch.dic) == 1:
                        do_consult(c, ch.j)
                        xs = [ch.dic[0]] * len(mine)
                    else:
                        do_read(c, ch.j, pg.p)
                        vals = page_values(ch, pg)
                        xs = [vals[r - pg.start] for r in mine]
                    for x in xs:
                        if x is not None:
                            nn += 1
                            tot += x
            for r, x in up.items():
                if r in alive and x is not None:
                    nn += 1
                    tot += x
            lines.append("prj %d %d %d" % (c, nn, tot))
    return lines


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as fh:
        sys.stdout.write("\n".join(run(fh.read())) + "\n")
