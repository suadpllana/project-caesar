import random
import sys


def gen(seed, n_max=40, k_max=3):
    rnd = random.Random(seed)
    g = rnd.choice([1, 2, 3, 5, 10])
    n = rnd.randint(1, n_max)
    k = rnd.randint(1, k_max)
    lines = ["seg %d %d %d" % (g, n, k)]

    col_true = [[None] * n for _ in range(k)]  # as-written value per row per col

    for c in range(k):
        pos = 0
        while pos < n:
            remaining = n - pos
            clen = rnd.randint(1, min(6, remaining))
            enc = rnd.choice(["p", "p", "d"])
            # generate this chunk's rows first (as-written), then pages, then dict/sum
            chunk_vals = []
            vmin, vmax = rnd.choice([(0, 5), (0, 20), (-10, 10), (100, 130)])
            for _ in range(clen):
                if rnd.random() < 0.2:
                    chunk_vals.append(None)
                else:
                    chunk_vals.append(rnd.randint(vmin, vmax))
            for i, v in enumerate(chunk_vals):
                col_true[c][pos + i] = v

            dic = None
            if enc == "d":
                distinct = sorted({v for v in chunk_vals if v is not None})
                if not distinct:
                    distinct = [rnd.randint(vmin, vmax)]
                dic = distinct
            s = sum(v for v in chunk_vals if v is not None)
            head = "ch %d %s %d" % (c, enc, s)
            if enc == "d":
                head += " %d %s" % (len(dic), " ".join(str(x) for x in dic))
            lines.append(head)

            # split chunk_vals into 1-3 pages
            ppos = 0
            while ppos < clen:
                prem = clen - ppos
                plen = rnd.randint(1, min(4, prem))
                pvals = chunk_vals[ppos:ppos + plen]
                nulls = sum(1 for v in pvals if v is None)
                nonnull = [v for v in pvals if v is not None]
                if nonnull:
                    mn, mx = min(nonnull), max(nonnull)
                else:
                    mn = mx = None
                form = "v"
                toks = pvals
                if enc == "d" and rnd.random() < 0.7:
                    form = "i"
                    toks = [None if v is None else dic.index(v) for v in pvals]
                exact = True
                wmn, wmx = mn, mx
                if mn is not None and rnd.random() < 0.4:
                    exact = False
                    # round outward is what we must be ABLE to recover from;
                    # actually generator must round the TRUE bounds INWARD per spec.
                    import math
                    wmn = -(-mn // g) * g if mn % g != 0 else mn  # ceil to multiple of g
                    wmx = (mx // g) * g  # floor to multiple of g
                    if wmn > wmx:
                        exact = True
                        wmn, wmx = mn, mx
                xtag = "e" if exact else "w"
                bmn = "-" if mn is None else str(wmn if not exact else mn)
                bmx = "-" if mx is None else str(wmx if not exact else mx)
                tokstr = " ".join("-" if t is None else str(t) for t in toks)
                lines.append("pg %d %d %s %s %s %s %s" % (plen, nulls, bmn, bmx, xtag, form, tokstr))
                ppos += plen
            pos += clen

    # updates
    up = {}
    for c in range(k):
        nup = rnd.randint(0, n // 3)
        rows = rnd.sample(range(n), min(nup, n))
        for r in rows:
            if rnd.random() < 0.15:
                up[(c, r)] = None
            else:
                up[(c, r)] = rnd.randint(-20, 140)
    for (c, r), v in sorted(up.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        lines.append("up %d %d %s" % (c, r, "-" if v is None else str(v)))

    gone = set()
    ndel = rnd.randint(0, n // 4)
    for r in rnd.sample(range(n), min(ndel, n)):
        lines.append("del %d" % r)
        gone.add(r)

    nq = rnd.randint(1, 3)
    for _ in range(nq):
        lines.append("qry")
        nc = rnd.randint(1, 4)
        kinds = ["ge", "le", "eq", "ne", "nn", "nu"]
        for _ in range(nc):
            kind = rnd.choice(kinds)
            c = rnd.randrange(k)
            if kind in ("nn", "nu"):
                lines.append("prd %s %d" % (kind, c))
            else:
                v = rnd.randint(-15, 145)
                lines.append("prd %s %d %d" % (kind, c, v))
        np_ = rnd.randint(1, 3)
        cols = [rnd.randrange(k) for _ in range(np_)]
        lines.append("prj " + " ".join(str(x) for x in cols))
        lines.append("end")

    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    seed = int(sys.argv[1])
    sys.stdout.write(gen(seed))
