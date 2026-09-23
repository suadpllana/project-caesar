"""Random small segment files, consistent with the format in the brief."""
import random


def rnd_inward(lo, hi, g):
    # round the true min up and the true max down to multiples of g
    rlo = -((-lo) // g) * g
    rhi = (hi // g) * g
    return rlo, rhi


def make(seed, big=False):
    R = random.Random(seed)
    g = R.choice([1, 1, 2, 2, 3, 5, 10])
    n = R.randint(1, big if big else 30)
    k = R.randint(1, 4)
    base = R.randint(-5, 30)
    spanv = R.choice([1, 2, 3, 5, 10, 30])
    lines = ["seg %d %d %d" % (g, n, k)]
    colvals = []
    for c in range(k):
        # chunk partition
        r = 0
        vals_c = []
        while r < n:
            cn = min(n - r, R.randint(1, R.choice([6, 14, 30])))
            # page partition
            sizes = []
            left = cn
            while left > 0:
                s = min(left, R.randint(1, R.choice([3, 6, 8])))
                sizes.append(s)
                left -= s
            enc = R.choice(["p", "d", "d"])
            if enc == "d":
                m = R.choice([0, 1, 1, 1, 2, 3, 4]) if R.random() < 0.2 else R.choice([1, 1, 2, 3])
                dic = sorted(R.sample(range(base, base + spanv + 5), min(m, spanv + 5)))
            else:
                dic = None
            pages = []
            csum = 0
            for s in sizes:
                form = "i" if (enc == "d" and dic and R.random() < 0.7) else "v"
                if enc == "d" and not dic and R.random() < 0.3:
                    form = "i"  # all-null i page with empty dict
                pnull = R.choice([0, 0, 0.2, 0.5, 1.0]) if R.random() < 0.9 else 1.0
                mode = R.random()
                const = R.randint(base, base + spanv)
                vals = []
                for _ in range(s):
                    if R.random() < pnull or (form == "i" and not dic):
                        vals.append(None)
                    elif form == "i":
                        vals.append(R.choice(dic))
                    elif mode < 0.3:
                        vals.append(const)
                    else:
                        vals.append(R.randint(base, base + spanv))
                nn = [x for x in vals if x is not None]
                u = s - len(nn)
                x = R.choice(["e", "w"])
                if not nn:
                    mn = mx = "-"
                else:
                    lo, hi = min(nn), max(nn)
                    if x == "w":
                        rlo, rhi = rnd_inward(lo, hi, g)
                        mn, mx = str(rlo), str(rhi)
                    else:
                        mn, mx = str(lo), str(hi)
                csum += sum(nn)
                if form == "i":
                    toks = ["-" if v is None else str(dic.index(v)) for v in vals]
                else:
                    toks = ["-" if v is None else str(v) for v in vals]
                pages.append("pg %d %d %s %s %s %s %s" % (s, u, mn, mx, x, form, " ".join(toks)))
                vals_c.extend(vals)
            if enc == "d":
                lines.append("ch %d d %d %d %s" % (c, csum, len(dic), " ".join(map(str, dic))))
            else:
                lines.append("ch %d p %d" % (c, csum))
            lines.extend(pages)
            r += cn
        colvals.append(vals_c)
    # updates: scattered, plus sometimes a contiguous block
    pu = R.choice([0.0, 0.05, 0.12, 0.3])
    for c in range(k):
        blk = None
        if R.random() < 0.3:
            a = R.randrange(n)
            blk = (a, a + R.randint(1, 12))
        for r in range(n):
            if R.random() < pu or (blk and blk[0] <= r < blk[1]):
                v = None if R.random() < 0.25 else R.randint(base - 2, base + spanv + 2)
                lines.append("up %d %d %s" % (c, r, "-" if v is None else str(v)))
    pd = R.choice([0.0, 0.03, 0.08, 0.2])
    for r in range(n):
        if R.random() < pd:
            lines.append("del %d" % r)
    nq = R.randint(1, 6)
    for _ in range(nq):
        lines.append("qry")
        for _ in range(R.randint(1, 8)):
            kind = R.choice(["ge", "le", "eq", "ne", "nn", "nu", "ge", "le", "eq", "ne"])
            c = R.randrange(k)
            if kind in ("nn", "nu"):
                lines.append("prd %s %d" % (kind, c))
            else:
                v = R.randint(base - g - 1, base + spanv + g + 1)
                lines.append("prd %s %d %d" % (kind, c, v))
        cols = [R.randrange(k) for _ in range(R.randint(1, 4))]
        lines.append("prj " + " ".join(map(str, cols)))
        lines.append("end")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    import sys
    sys.stdout.write(make(int(sys.argv[1])))
