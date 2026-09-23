"""Random segment files for cross-checking app/ against model.py."""
import random


def ceil_to(x, g):
    return -((-x) // g) * g


def floor_to(x, g):
    return (x // g) * g


def parts(total, lo, hi, rng):
    out = []
    left = total
    while left > 0:
        k = rng.randint(lo, hi)
        if k >= left or left - k < lo and rng.random() < 0.7:
            k = left
        out.append(k)
        left -= k
    return out


def make(rng, n=None, k=None, chunk=(1, 12), page=(1, 5), nq=None, ncond=None, big=False):
    g = rng.choice([1, 1, 2, 2, 3, 5, 10, 25])
    if n is None:
        n = rng.randint(1, 40)
    if k is None:
        k = rng.randint(1, 4)
    lines = ["seg %d %d %d" % (g, n, k)]
    colinfo = []
    for c in range(k):
        base = rng.choice([0, 0, 10, 100, -20])
        span = rng.choice([1, 2, 5, 12, 40, 120])
        colinfo.append((base, span))
        pnull = rng.choice([0.0, 0.05, 0.2, 0.5])
        for chn in parts(n, *chunk, rng):
            enc = rng.choice(["p", "d", "d"])
            dic = None
            if enc == "d":
                m = rng.choice([1, 1, 2, 3, 4, 6])
                dic = sorted(rng.sample(range(base, base + span + m + 1), m))
                lines.append("ch %d d %d %s" % (c, m, " ".join(map(str, dic))))
            else:
                lines.append("ch %d p" % c)
            for pn in parts(chn, *page, rng):
                style = rng.random()
                form = "i" if (dic is not None and rng.random() < 0.75) else "v"
                if form == "i":
                    pool = list(range(len(dic)))
                    if rng.random() < 0.3:
                        pool = [rng.randrange(len(dic))]
                    idx = []
                    for _ in range(pn):
                        if style < 0.1 or rng.random() < pnull:
                            idx.append(None)
                        else:
                            idx.append(rng.choice(pool))
                    vals = [None if t is None else dic[t] for t in idx]
                    toks = ["-" if t is None else str(t) for t in idx]
                else:
                    if style < 0.1:
                        vals = [None] * pn
                    elif style < 0.25:
                        cv = rng.randint(base, base + span)
                        vals = [None if rng.random() < pnull else cv for _ in range(pn)]
                    else:
                        lo = rng.randint(base, base + span)
                        hi = rng.randint(lo, base + span)
                        vals = [None if rng.random() < pnull else rng.randint(lo, hi) for _ in range(pn)]
                    toks = ["-" if x is None else str(x) for x in vals]
                nn = [x for x in vals if x is not None]
                u = pn - len(nn)
                if nn:
                    a, b = min(nn), max(nn)
                    if rng.random() < 0.45:
                        x = "w"
                        mn, mx = ceil_to(a, g), floor_to(b, g)
                    else:
                        x = "e"
                        mn, mx = a, b
                    lines.append("pg %d %d %d %d %s %d %s %s" % (pn, u, mn, mx, x, sum(nn), form, " ".join(toks)))
                else:
                    x = rng.choice("ew")
                    lines.append("pg %d %d - - %s 0 %s %s" % (pn, u, x, form, " ".join(toks)))
    # updates and deletes
    nup = rng.randint(0, max(1, n * k // (3 if not big else 4)))
    seen = set()
    for _ in range(nup):
        c = rng.randrange(k)
        r = rng.randrange(n)
        if (c, r) in seen:
            continue
        seen.add((c, r))
        base, span = colinfo[c]
        v = "-" if rng.random() < 0.2 else str(rng.randint(base - 2, base + span + 2))
        lines.append("up %d %d %s" % (c, r, v))
    for _ in range(rng.randint(0, max(1, n // 6))):
        lines.append("del %d" % rng.randrange(n))
    if nq is None:
        nq = rng.randint(1, 4)
    for _ in range(nq):
        lines.append("qry")
        nc = ncond if ncond is not None else rng.randint(1, 6)
        for _ in range(nc):
            c = rng.randrange(k)
            kind = rng.choice(["ge", "le", "eq", "ne", "nn", "nu", "ge", "le", "eq", "ne"])
            if kind in ("nn", "nu"):
                lines.append("prd %s %d" % (kind, c))
            else:
                base, span = colinfo[c]
                v = rng.randint(base - 3, base + span + 3)
                lines.append("prd %s %d %d" % (kind, c, v))
        cols = [rng.randrange(k) for _ in range(rng.randint(1, 4))]
        lines.append("prj " + " ".join(map(str, cols)))
        lines.append("end")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    import sys
    print(make(random.Random(int(sys.argv[1]))), end="")
