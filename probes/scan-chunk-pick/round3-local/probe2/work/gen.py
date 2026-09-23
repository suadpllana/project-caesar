"""Random segment files for cross-checking the scanner against ref.py."""
import random
import sys


def split(total, lo, hi, rng):
    out = []
    left = total
    while left > 0:
        k = rng.randint(lo, hi)
        if k > left:
            k = left
        out.append(k)
        left -= k
    return out


def make(seed):
    rng = random.Random(seed)
    G = rng.choice([1, 2, 3, 5, 10, 25])
    N = rng.randint(1, rng.choice([12, 40, 120, 300]))
    K = rng.randint(1, 4)
    vlo = rng.choice([0, 0, 5])
    vhi = vlo + rng.choice([3, 8, 20, 60, 200])
    lines = ["seg %d %d %d" % (G, N, K)]
    chmax = rng.choice([4, 10, 30, 80])
    pgmax = rng.choice([1, 3, 6, 12])
    for c in range(K):
        for csize in split(N, 1, chmax, rng):
            enc = rng.choice("pdd")
            dic = None
            if enc == "d":
                m = rng.choice([1, 1, 2, 3, 5, 8])
                pool = list(range(vlo, vhi + 1))
                m = min(m, len(pool))
                dic = sorted(rng.sample(pool, m))
                lines.append("ch %d d %d %s" % (c, m, " ".join(map(str, dic))))
            else:
                lines.append("ch %d p" % c)
            for n in split(csize, 1, pgmax, rng):
                form = "i" if (dic is not None and rng.random() < 0.75) else "v"
                mode = rng.random()
                if mode < 0.12:
                    pnull = 1.0
                elif mode < 0.45:
                    pnull = 0.0
                else:
                    pnull = rng.choice([0.1, 0.3, 0.6])
                narrow = rng.random() < 0.25
                if narrow:
                    base = rng.randint(vlo, vhi)
                vals = []
                idx = []
                for _ in range(n):
                    if rng.random() < pnull:
                        vals.append(None)
                        idx.append(None)
                    elif form == "i":
                        t = rng.randrange(len(dic)) if not narrow else 0
                        idx.append(t)
                        vals.append(dic[t])
                    else:
                        x = base if narrow and rng.random() < 0.8 else rng.randint(vlo, vhi)
                        vals.append(x)
                        idx.append(x)
                nn = [x for x in vals if x is not None]
                u = n - len(nn)
                if not nn:
                    mn = mx = "-"
                    x = rng.choice("ew")
                else:
                    x = "e" if (G == 1 or rng.random() < 0.5) else "w"
                    if x == "e":
                        mn, mx = min(nn), max(nn)
                    else:
                        mn = -(-min(nn) // G) * G
                        mx = max(nn) // G * G
                toks = " ".join("-" if t is None else str(t) for t in idx)
                lines.append("pg %d %d %s %s %s %d %s %s" % (n, u, mn, mx, x, sum(nn), form, toks))
    # updates
    for c in range(K):
        rows = rng.sample(range(N), rng.randint(0, N // 3))
        for r in rows:
            if rng.random() < 0.25:
                v = "-"
            else:
                v = str(rng.randint(vlo, vhi))
            lines.append("up %d %d %s" % (c, r, v))
    for r in rng.sample(range(N), rng.randint(0, N // 4)):
        lines.append("del %d" % r)
    for _ in range(rng.randint(1, 5)):
        lines.append("qry")
        for _ in range(rng.randint(1, 6)):
            kind = rng.choice(["ge", "le", "eq", "ne", "nn", "nu", "ge", "le", "eq", "ne"])
            c = rng.randrange(K)
            if kind in ("nn", "nu"):
                lines.append("prd %s %d" % (kind, c))
            else:
                v = rng.randint(vlo - 3, vhi + 3)
                lines.append("prd %s %d %d" % (kind, c, v))
        cols = [rng.randrange(K) for _ in range(rng.randint(1, 4))]
        lines.append("prj " + " ".join(map(str, cols)))
        lines.append("end")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.stdout.write(make(int(sys.argv[1])))
