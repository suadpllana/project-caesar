"""Mid-sized files shaped like the shipped wide and deep ones."""
import random


def inward(lo, hi, g):
    return -((-lo) // g) * g, (hi // g) * g


def make(seed, n=None):
    R = random.Random(seed)
    wide = R.random() < 0.6
    g = R.choice([25, 25, 10, 2, 1])
    k = R.randint(4, 5) if wide else 4
    n = n or R.randint(120, 400)
    lines = ["seg %d %d %d" % (g, n, k)]
    for c in range(k):
        if wide:
            lo_v, hi_v = (300, 700) if R.random() < 0.7 else (0, 40)
        else:
            lo_v, hi_v = 0, R.choice([39, 119, 399])
        r = 0
        while r < n:
            cn = min(n - r, R.randint(16, 40) if wide else R.randint(60, 140))
            if n - r - cn < 10:
                cn = n - r
            sizes = []
            left = cn
            while left > 0:
                s = min(left, R.randint(4, 12) if wide else R.randint(15, 40))
                if left - s < 3:
                    s = left
                sizes.append(s)
                left -= s
            kind = R.random()
            if kind < 0.35:
                enc, dic = "p", None
            elif kind < 0.6:
                enc = "d"
                dic = [R.randrange(lo_v, hi_v + 1)]
            else:
                enc = "d"
                m = R.randint(2, 30)
                dic = sorted(set(R.randrange(lo_v, hi_v + 1) for _ in range(m)))
            csum = 0
            pages = []
            for s in sizes:
                form = "i" if enc == "d" and R.random() < 0.65 else "v"
                pn = R.choice([0, 0, 0.1, 0.4])
                style = R.random()
                vals = []
                for _ in range(s):
                    if R.random() < pn:
                        vals.append(None)
                    elif form == "i":
                        vals.append(R.choice(dic))
                    elif dic and style < 0.5:
                        vals.append(dic[0] if R.random() < 0.7 else R.randrange(lo_v, hi_v + 1))
                    elif style < 0.7:
                        vals.append(R.randrange(lo_v, lo_v + 3 * g + 2))
                    else:
                        vals.append(R.randrange(lo_v, hi_v + 1))
                nn = [v for v in vals if v is not None]
                x = R.choice(["e", "w"])
                if nn:
                    a, b = min(nn), max(nn)
                    if x == "w":
                        a, b = inward(a, b, g)
                    mn, mx = str(a), str(b)
                else:
                    mn = mx = "-"
                csum += sum(nn)
                if form == "i":
                    toks = ["-" if v is None else str(dic.index(v)) for v in vals]
                else:
                    toks = ["-" if v is None else str(v) for v in vals]
                pages.append("pg %d %d %s %s %s %s %s" % (s, s - len(nn), mn, mx, x, form, " ".join(toks)))
            if enc == "d":
                lines.append("ch %d d %d %d %s" % (c, csum, len(dic), " ".join(map(str, dic))))
            else:
                lines.append("ch %d p %d" % (c, csum))
            lines.extend(pages)
            r += cn
    for c in range(k):
        done = set()
        for _ in range(R.randint(0, 3)):
            a = R.randrange(n)
            for r in range(a, min(n, a + R.randint(5, 40))):
                done.add(r)
        for r in range(n):
            if r in done or R.random() < 0.05:
                v = None if R.random() < 0.1 else R.randrange(0, 720)
                lines.append("up %d %d %s" % (c, r, "-" if v is None else v))
    for r in range(n):
        if R.random() < 0.02:
            lines.append("del %d" % r)
    for _ in range(3):
        lines.append("qry")
        for _ in range(R.randint(5, 8)):
            kd = R.choice(["ge", "le", "eq", "ne", "nn", "nu", "le", "ne", "nn"])
            c = R.randrange(k)
            if kd in ("nn", "nu"):
                lines.append("prd %s %d" % (kd, c))
            else:
                lines.append("prd %s %d %d" % (kd, c, R.randrange(0, 720) if R.random() < 0.5 else R.randrange(0, 45)))
        lines.append("prj " + " ".join(str(R.randrange(k)) for _ in range(R.randint(1, 4))))
        lines.append("end")
    return "\n".join(lines) + "\n"
