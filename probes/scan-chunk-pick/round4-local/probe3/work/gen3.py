"""Wide/deep-like files at a size the literal reference can still check."""
import random
from gen import page_line, split


def make(seed, N=None):
    rng = random.Random(seed * 104729 + 3)
    deep = rng.random() < 0.4
    G = 25 if rng.random() < 0.7 else rng.choice([2, 3, 10])
    if N is None:
        N = rng.randint(300, 900)
    K = rng.randint(4, 5) if not deep else 4
    lines = ["seg %d %d %d" % (G, N, K)]
    rngs = []
    for c in range(K):
        base = rng.choice([0, 300, 50])
        span = rng.choice([40, 400, 120])
        rngs.append((base, span))
        for csz in (split(rng, N, 16, 40) if not deep else split(rng, N, 150, 300)):
            psizes = split(rng, csz, 4, 12) if not deep else split(rng, csz, 30, 90)
            isd = rng.random() < 0.3
            if isd:
                pool = list(range(base, base + span + 1))
                m = min(len(pool), rng.choice([1, 2, 5, 12, 38]))
                dic = sorted(rng.sample(pool, m))
            else:
                dic = None
            pnull = rng.choice([0, 0.05, 0.15])
            pls = []
            tot = 0
            for ps in psizes:
                form = "i" if (isd and rng.random() < 0.8) else "v"
                allnull = rng.random() < 0.01
                konst = rng.random() < 0.03
                kval = rng.choice(dic) if form == "i" else rng.randint(base, base + span)
                lo = rng.randint(base, base + span)
                hi = min(base + span, lo + rng.randint(0, span))
                vals = []
                for _ in range(ps):
                    if allnull or rng.random() < pnull:
                        vals.append(None)
                    elif form == "i":
                        vals.append(kval if konst else rng.choice(dic))
                    else:
                        vals.append(kval if konst else rng.randint(lo, hi))
                tot += sum(v for v in vals if v is not None)
                pls.append(page_line(rng, G, vals, form, dic, False))
            if isd:
                lines.append("ch %d d %d %d %s" % (c, tot, len(dic), " ".join(map(str, dic))))
            else:
                lines.append("ch %d p %d" % (c, tot))
            lines.extend(pls)
    for c in range(K):
        for r in range(N):
            if rng.random() < 0.05:
                v = "-" if rng.random() < 0.1 else str(rng.randint(rngs[c][0], rngs[c][0] + rngs[c][1]))
                lines.append("up %d %d %s" % (c, r, v))
    for r in range(N):
        if rng.random() < 0.01:
            lines.append("del %d" % r)
    kinds = ["ge", "le", "eq", "ne", "nn", "nu", "nn", "le", "ge", "ne"]
    for _ in range(3):
        lines.append("qry")
        for _ in range(8 if not deep else 7):
            k = rng.choice(kinds)
            c = rng.randrange(K)
            if k in ("nn", "nu"):
                lines.append("prd %s %d" % (k, c))
            else:
                b0, s0 = rngs[c]
                lines.append("prd %s %d %d" % (k, c, rng.randint(b0 - 3, b0 + s0 + 3)))
        lines.append("prj " + " ".join(str(rng.randrange(K)) for _ in range(3)))
        lines.append("end")
    return "\n".join(lines) + "\n"
