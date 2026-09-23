"""Random segment files shaped to hit the corners of the brief."""
import random


def page_line(rng, G, vals, form, dic, loose):
    n = len(vals)
    nn = [v for v in vals if v is not None]
    u = n - len(nn)
    if not nn:
        mn = mx = "-"
        x = rng.choice("ew")
    else:
        lo, hi = min(nn), max(nn)
        x = rng.choice("ew")
        if x == "e":
            if loose and rng.random() < 0.3:
                lo -= rng.randint(0, 3)
                hi += rng.randint(0, 3)
            mn, mx = lo, hi
        else:
            mn = -(-lo // G) * G
            mx = (hi // G) * G
    if form == "i":
        toks = ["-" if v is None else str(dic.index(v)) for v in vals]
    else:
        toks = ["-" if v is None else str(v) for v in vals]
    return "pg %d %d %s %s %s %s %s" % (n, u, mn, mx, x, form, " ".join(toks))


def split(rng, total, lo, hi):
    out = []
    left = total
    while left > 0:
        s = min(left, rng.randint(lo, hi))
        out.append(s)
        left -= s
    return out


def make(seed):
    rng = random.Random(seed)
    G = rng.choice([1, 1, 2, 2, 3, 5, 10, 25])
    N = rng.randint(1, 70)
    K = rng.randint(1, 4)
    vlo = rng.choice([0, -10, 5, -3])
    vhi = vlo + rng.choice([0, 1, 2, 4, 8, 15, 40, 100])
    lines = ["seg %d %d %d" % (G, N, K)]
    loose = rng.random() < 0.2
    cols_vals = []
    for c in range(K):
        colv = []
        for csz in split(rng, N, 1, rng.choice([3, 6, 12, 25])):
            psizes = split(rng, csz, 1, rng.choice([1, 2, 4, 7]))
            isd = rng.random() < 0.5
            pnull = rng.choice([0, 0, 0.1, 0.3, 0.7, 1.0])
            if isd:
                m = rng.choice([1, 1, 1, 2, 3, 5])
                pool = list(range(vlo, vhi + 1))
                m = min(m, len(pool))
                dic = sorted(rng.sample(pool, m))
            else:
                dic = None
            pls = []
            tot = 0
            for ps in psizes:
                form = "i" if (isd and rng.random() < 0.8) else "v"
                allnull = rng.random() < 0.08
                vals = []
                konst = rng.random() < 0.15
                kval = rng.randint(vlo, vhi) if not (form == "i") else rng.choice(dic)
                for _ in range(ps):
                    if allnull or rng.random() < pnull:
                        vals.append(None)
                    elif form == "i":
                        vals.append(kval if konst else rng.choice(dic))
                    else:
                        vals.append(kval if konst else rng.randint(vlo, vhi))
                tot += sum(v for v in vals if v is not None)
                colv.extend(vals)
                pls.append(page_line(rng, G, vals, form, dic, loose))
            if isd:
                lines.append("ch %d d %d %d %s" % (c, tot, len(dic), " ".join(map(str, dic))))
            else:
                lines.append("ch %d p %d" % (c, tot))
            lines.extend(pls)
        cols_vals.append(colv)
    # updates
    for c in range(K):
        for r in range(N):
            if rng.random() < 0.12:
                v = "-" if rng.random() < 0.25 else str(rng.randint(vlo - 2, vhi + 2))
                lines.append("up %d %d %s" % (c, r, v))
    for r in range(N):
        if rng.random() < 0.08:
            lines.append("del %d" % r)
    nq = rng.randint(1, 4)
    kinds = ["ge", "le", "eq", "ne", "nn", "nu"]
    for _ in range(nq):
        lines.append("qry")
        for _ in range(rng.randint(1, 6)):
            k = rng.choice(kinds)
            c = rng.randrange(K)
            if k in ("nn", "nu"):
                lines.append("prd %s %d" % (k, c))
            else:
                lines.append("prd %s %d %d" % (k, c, rng.randint(vlo - 3, vhi + 3)))
        pc = [rng.randrange(K) for _ in range(rng.randint(1, 4))]
        lines.append("prj " + " ".join(map(str, pc)))
        lines.append("end")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    import sys
    sys.stdout.write(make(int(sys.argv[1])))
