"""Medium random files: more rows, more chunks, more conditions, skewed values."""
import random
from gen import page_line, split


def make(seed):
    rng = random.Random(seed * 7919 + 17)
    G = rng.choice([1, 2, 3, 5, 25])
    N = rng.randint(80, 260)
    K = rng.randint(2, 5)
    vlo = rng.choice([0, -20, 3])
    vhi = vlo + rng.choice([3, 10, 30, 120])
    lines = ["seg %d %d %d" % (G, N, K)]
    for c in range(K):
        for csz in split(rng, N, rng.choice([1, 4, 10]), rng.choice([12, 30, 60])):
            psizes = split(rng, csz, 1, rng.choice([2, 5, 12]))
            isd = rng.random() < 0.45
            pnull = rng.choice([0, 0, 0.05, 0.2, 0.5])
            skew = rng.random() < 0.5
            if isd:
                pool = list(range(vlo, vhi + 1))
                m = min(len(pool), rng.choice([1, 1, 2, 3, 6, 12]))
                dic = sorted(rng.sample(pool, m))
            else:
                dic = None
            pls = []
            tot = 0
            for ps in psizes:
                form = "i" if (isd and rng.random() < 0.85) else "v"
                allnull = rng.random() < 0.05
                konst = rng.random() < 0.1
                kval = rng.choice(dic) if form == "i" else rng.randint(vlo, vhi)
                vals = []
                for _ in range(ps):
                    if allnull or rng.random() < pnull:
                        vals.append(None)
                    elif form == "i":
                        vals.append(kval if konst else rng.choice(dic))
                    elif konst:
                        vals.append(kval)
                    elif skew:
                        # mostly near the top with a rare low outlier: estimates run low
                        vals.append(vhi - rng.randint(0, 2) if rng.random() < 0.85 else rng.randint(vlo, vhi))
                    else:
                        vals.append(rng.randint(vlo, vhi))
                tot += sum(v for v in vals if v is not None)
                pls.append(page_line(rng, G, vals, form, dic, False))
            if isd:
                lines.append("ch %d d %d %d %s" % (c, tot, len(dic), " ".join(map(str, dic))))
            else:
                lines.append("ch %d p %d" % (c, tot))
            lines.extend(pls)
    pu = rng.choice([0.0, 0.02, 0.1])
    for c in range(K):
        for r in range(N):
            if rng.random() < pu:
                v = "-" if rng.random() < 0.2 else str(rng.randint(vlo - 2, vhi + 2))
                lines.append("up %d %d %s" % (c, r, v))
    pd = rng.choice([0.0, 0.01, 0.05])
    for r in range(N):
        if rng.random() < pd:
            lines.append("del %d" % r)
    kinds = ["ge", "ge", "le", "le", "eq", "ne", "nn", "nu"]
    for _ in range(rng.randint(1, 4)):
        lines.append("qry")
        for _ in range(rng.randint(1, 8)):
            k = rng.choice(kinds)
            c = rng.randrange(K)
            if k in ("nn", "nu"):
                lines.append("prd %s %d" % (k, c))
            else:
                lines.append("prd %s %d %d" % (k, c, rng.randint(vlo - 2, vhi + 2)))
        lines.append("prj " + " ".join(str(rng.randrange(K)) for _ in range(rng.randint(1, 4))))
        lines.append("end")
    return "\n".join(lines) + "\n"
