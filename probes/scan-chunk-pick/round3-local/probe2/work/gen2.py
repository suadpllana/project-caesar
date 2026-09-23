"""Scaled-down segment files shaped like wide.txt and deep.txt."""
import random
import sys

RANGES = [(300, 706), (0, 46), (300, 426), (0, 126), (0, 406)]


def split(total, lo, hi, rng):
    out = []
    left = total
    while left > 0:
        k = rng.randint(lo, hi)
        if left - k < lo:
            k = left
        out.append(k)
        left -= k
    return out


def make(seed, shape):
    rng = random.Random(seed * 7 + (1 if shape == "deep" else 0))
    G = 25
    if shape == "wide":
        N = rng.randint(300, 900)
        K = 5
        cl, chh, pl, ph = 16, 40, 4, 12
        nq, nc = 3, 8
    else:
        N = rng.randint(1500, 3000)
        K = 4
        cl, chh, pl, ph = 150, 260, 25, 60
        nq, nc = 3, 7
    lines = ["seg %d %d %d" % (G, N, K)]
    ranges = [rng.choice(RANGES) for _ in range(K)]
    for c in range(K):
        lo, hi = ranges[c]
        for csize in split(N, cl, chh, rng):
            dic = None
            if rng.random() < 0.3:
                m = rng.randint(1, 12)
                centre = rng.randint(lo, hi)
                pool = list(range(max(lo, centre - 30), min(hi, centre + 30) + 1))
                dic = sorted(rng.sample(pool, min(m, len(pool))))
                lines.append("ch %d d %d %s" % (c, len(dic), " ".join(map(str, dic))))
            else:
                lines.append("ch %d p" % c)
            for n in split(csize, pl, ph, rng):
                form = "i" if dic is not None and rng.random() < 0.8 else "v"
                r = rng.random()
                pnull = 1.0 if r < 0.01 else (0.0 if r < 0.45 else rng.choice([0.05, 0.1, 0.2]))
                centre = rng.randint(lo, hi)
                spread = rng.choice([0, 3, 15, 60, 200])
                toks = []
                vals = []
                for _ in range(n):
                    if rng.random() < pnull:
                        toks.append("-")
                        vals.append(None)
                    elif form == "i":
                        t = rng.randrange(len(dic))
                        toks.append(str(t))
                        vals.append(dic[t])
                    else:
                        x = min(hi, max(lo, centre + rng.randint(-spread, spread)))
                        toks.append(str(x))
                        vals.append(x)
                nn = [x for x in vals if x is not None]
                if not nn:
                    lines.append("pg %d %d - - %s 0 %s %s" % (n, n, rng.choice("ew"), form, " ".join(toks)))
                    continue
                if rng.random() < 0.5:
                    x, mn, mx = "e", min(nn), max(nn)
                else:
                    x, mn, mx = "w", -(-min(nn) // G) * G, max(nn) // G * G
                lines.append("pg %d %d %d %d %s %d %s %s" % (n, n - len(nn), mn, mx, x, sum(nn), form, " ".join(toks)))
    for c in range(K):
        lo, hi = ranges[c]
        for r in rng.sample(range(N), N // 20):
            lines.append("up %d %d %s" % (c, r, "-" if rng.random() < 0.3 else rng.randint(lo, hi)))
    for r in rng.sample(range(N), N // 100):
        lines.append("del %d" % r)
    for _ in range(nq):
        lines.append("qry")
        for _ in range(nc):
            c = rng.randrange(K)
            lo, hi = ranges[c]
            kind = rng.choice(["ge", "le", "eq", "ne", "nn", "nu", "le", "ge", "nn"])
            if kind in ("nn", "nu"):
                lines.append("prd %s %d" % (kind, c))
            else:
                lines.append("prd %s %d %d" % (kind, c, rng.randint(lo - 5, hi + 5)))
        lines.append("prj " + " ".join(str(rng.randrange(K)) for _ in range(3)))
        lines.append("end")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.stdout.write(make(int(sys.argv[1]), sys.argv[2]))
