"""Random, internally consistent segment files for differential testing."""
import random


def _header(G, vals, wide):
    nn = [x for x in vals if x is not None]
    u = len(vals) - len(nn)
    if not nn:
        return u, "-", "-", ("w" if wide else "e"), 0
    lo = min(nn)
    hi = max(nn)
    if wide:
        mn = -((-lo) // G) * G  # rounded inward: low up, high down
        mx = (hi // G) * G
        return u, str(mn), str(mx), "w", sum(nn)
    return u, str(lo), str(hi), "e", sum(nn)


def gen(rng, N=None, K=None, G=None, chunk=None, page=None, nq=None, ncond=None,
        prof=None):
    prof = prof or {}
    if N is None:
        N = rng.randint(1, 60)
    if K is None:
        K = rng.randint(1, 4)
    if G is None:
        G = rng.choice([1, 2, 3, 5, 10, 25, 100])
    if chunk is None:
        a = rng.randint(1, 12)
        chunk = (a, a + rng.randint(0, 20))
    if page is None:
        a = rng.randint(1, 6)
        page = (a, a + rng.randint(0, 8))
    if nq is None:
        nq = rng.randint(1, 4)
    lines = ["seg %d %d %d" % (G, N, K)]
    colinfo = []
    written = [[None] * N for _ in range(K)]
    for c in range(K):
        base = rng.choice([0, 0, 300, -40, 1000])
        span = rng.choice([1, 3, 8, 20, 60, 127, 400])
        null_rate = rng.choice([0, 0, 0.05, 0.2, 0.5, 0.9])
        pd = rng.choice([0, 0.3, 0.6, 1.0])
        pw = rng.choice([0, 0.3, 0.5, 1.0])
        colinfo.append((base, span))
        r = 0
        while r < N:
            csz = rng.randint(*chunk)
            if prof.get("longtail") and N - r - csz < chunk[0]:
                csz = N - r
            csz = max(1, min(csz, N - r))
            enc = "d" if rng.random() < pd else "p"
            dic = None
            if enc == "d":
                m = rng.choice([0, 1, 1, 1, 2, 3, 4, 6, 10])
                pool = range(base, base + max(span, m) + 1)
                dic = sorted(rng.sample(pool, m))
                lines.append(("ch %d d %d %s" % (c, m, " ".join(map(str, dic)))).rstrip())
            else:
                lines.append("ch %d p" % c)
            pr = 0
            while pr < csz:
                psz = rng.randint(*page)
                if prof.get("longtail") and csz - pr - psz < page[0]:
                    psz = csz - pr
                psz = max(1, min(psz, csz - pr))
                form = "v"
                if dic is not None and rng.random() < 0.75:
                    form = "i"
                if form == "i" and not dic:
                    mode = "allnull"
                else:
                    mode = rng.choice(["mix", "mix", "mix", "nonull", "allnull", "const",
                                       "constnull", "narrow"])
                vals = []
                if form == "i":
                    if mode == "const" or mode == "constnull":
                        pick = [rng.randrange(len(dic))]
                    elif mode == "narrow":
                        a = rng.randrange(len(dic))
                        pick = list(range(a, min(len(dic), a + 2)))
                    else:
                        pick = list(range(len(dic))) if dic else []
                    toks = []
                    for _ in range(psz):
                        isnull = (mode == "allnull" or
                                  (mode in ("mix", "constnull", "narrow") and rng.random() < max(null_rate, 0.15 if mode == "constnull" else 0)))
                        if isnull or not pick:
                            toks.append("-")
                            vals.append(None)
                        else:
                            ix = rng.choice(pick)
                            toks.append(str(ix))
                            vals.append(dic[ix])
                else:
                    cv = base + rng.randint(0, span)
                    a = base + rng.randint(0, span)
                    toks = []
                    for _ in range(psz):
                        isnull = (mode == "allnull" or
                                  (mode in ("mix", "constnull", "narrow") and rng.random() < max(null_rate, 0.15 if mode == "constnull" else 0)))
                        if isnull:
                            toks.append("-")
                            vals.append(None)
                            continue
                        if mode in ("const", "constnull"):
                            x = cv
                        elif mode == "narrow":
                            x = a + rng.randint(0, 2)
                        elif dic is not None and rng.random() < 0.5 and dic:
                            x = rng.choice(dic)
                        else:
                            x = base + rng.randint(0, span)
                        toks.append(str(x))
                        vals.append(x)
                wide = rng.random() < pw
                u, mn, mx, x, s = _header(G, vals, wide)
                lines.append("pg %d %d %s %s %s %d %s %s" % (psz, u, mn, mx, x, s, form, " ".join(toks)))
                st = r + pr
                for i, val in enumerate(vals):
                    written[c][st + i] = val
                pr += psz
            r += csz
    # updates and deletes
    pup = rng.choice([0, 0.02, 0.1, 0.3])
    for c in range(K):
        base, span = colinfo[c]
        for r in range(N):
            if rng.random() < pup:
                if rng.random() < 0.25:
                    lines.append("up %d %d -" % (c, r))
                else:
                    lines.append("up %d %d %d" % (c, r, base + rng.randint(-2, span + 2)))
    pdel = rng.choice([0, 0.01, 0.05, 0.2])
    for r in range(N):
        if rng.random() < pdel:
            lines.append("del %d" % r)
    # queries
    kinds = ["ge", "le", "eq", "ne", "nn", "nu"]
    for _ in range(nq):
        lines.append("qry")
        nc = ncond if ncond is not None else rng.randint(1, 6)
        prev = None
        for _ in range(nc):
            if prev is not None and rng.random() < 0.15:
                lines.append(prev)
                continue
            kind = rng.choice(kinds)
            c = rng.randrange(K)
            if kind in ("nn", "nu"):
                ln = "prd %s %d" % (kind, c)
            else:
                base, span = colinfo[c]
                t = rng.random()
                if t < 0.5:
                    col = [x for x in written[c] if x is not None]
                    v = rng.choice(col) + rng.choice([-1, 0, 0, 0, 1]) if col else base
                elif t < 0.8:
                    v = base + rng.randint(-3, span + 3)
                else:
                    v = rng.choice([base - 1000, base + span + 1000, base, base + span])
                ln = "prd %s %d %d" % (kind, c, v)
            lines.append(ln)
            prev = ln
        np_ = rng.randint(1, 4)
        cols = [rng.randrange(K) for _ in range(np_)]
        lines.append("prj " + " ".join(map(str, cols)))
        lines.append("end")
    return "\n".join(lines) + "\n"


def wide_like(rng, N=1500):
    return gen(rng, N=N, K=5, G=25, chunk=(16, 40), page=(4, 12), nq=3, ncond=8,
               prof={"longtail": True})


def deep_like(rng, N=4000):
    return gen(rng, N=N, K=4, G=25, chunk=(150, 260), page=(20, 60), nq=3, ncond=7,
               prof={"longtail": True})
