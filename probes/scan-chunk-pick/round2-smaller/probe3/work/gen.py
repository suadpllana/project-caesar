import random
import sys


def gen(seed, n_rows=60, n_cols=3, g=8, n_queries=3):
    rnd = random.Random(seed)
    lines = []
    lines.append("seg %d %d %d" % (g, n_rows, n_cols))
    col_chunks = [[] for _ in range(n_cols)]
    for c in range(n_cols):
        start = 0
        while start < n_rows:
            n = rnd.randint(1, 9)
            n = min(n, n_rows - start)
            nulls = rnd.randint(0, n)
            enc = rnd.choice(["p", "p", "d"])
            exact = rnd.choice(["e", "e", "w"])
            have = n - nulls
            if have == 0:
                mn = mx = None
                vals = [None] * n
            else:
                if exact == "w":
                    # Anchor lo itself on a multiple of g and force it
                    # to actually appear, so an inward-rounded pair
                    # (rl=lo at least) is always well defined regardless
                    # of where the rest of the sample lands.
                    lo = rnd.randint(-5, 5) * g
                    span = rnd.randint(0, 15)
                    hi = lo + span
                    vals = [rnd.randint(lo, hi) for _ in range(have)] + [None] * nulls
                    vals[0] = lo
                else:
                    lo = rnd.randint(-20, 20)
                    span = rnd.randint(0, 15)
                    hi = lo + span
                    vals = [rnd.randint(lo, hi) for _ in range(have)] + [None] * nulls
                rnd.shuffle(vals)
                nonnull = [v for v in vals if v is not None]
                mn, mx = min(nonnull), max(nonnull)
                if exact == "w":
                    # round inward to a multiple of g, record that pair
                    # per the 'w' contract.
                    rl = (mn // g) * g
                    if rl < mn:
                        rl += g
                    rh = (mx // g + 1) * g
                    if rh > mx:
                        rh -= g
                    assert rl <= rh, (mn, mx, g, rl, rh)
                    assert rl - (g - 1) <= mn and mx <= rh + (g - 1)
                    mn_rec, mx_rec = rl, rh
                else:
                    mn_rec, mx_rec = mn, mx
            f = ["ch", str(c), str(n), str(nulls),
                 "-" if have == 0 else str(mn_rec),
                 "-" if have == 0 else str(mx_rec),
                 exact, enc]
            if enc == "p":
                f.extend("-" if v is None else str(v) for v in vals)
            else:
                nonnull_vals = sorted(set(v for v in vals if v is not None))
                star_prob = 0.15
                # An all-null 'd' chunk has an empty dictionary: with no
                # non-null row, no entry could ever appear (the
                # "each entry appears at least once" contract requires
                # have > 0 for any entries to exist at all).
                dic = list(nonnull_vals)
                f.append(str(len(dic)))
                f.extend(str(x) for x in dic)
                for v in vals:
                    if v is None:
                        f.append("-")
                    elif rnd.random() < star_prob:
                        f.append("*%d" % v)
                    else:
                        f.append(str(dic.index(v)))
            lines.append(" ".join(f))
            col_chunks[c].append((start, n))
            start += n

    # updates
    n_updates = rnd.randint(0, n_rows)
    used = set()
    for _ in range(n_updates):
        c = rnd.randrange(n_cols)
        r = rnd.randrange(n_rows)
        key = (c, r)
        if key in used:
            continue
        used.add(key)
        if rnd.random() < 0.2:
            v = "-"
        else:
            v = str(rnd.randint(-25, 25))
        lines.append("up %d %d %s" % (c, r, v))

    # deletes
    n_del = rnd.randint(0, n_rows // 3)
    delset = rnd.sample(range(n_rows), n_del) if n_del else []
    for r in delset:
        lines.append("del %d" % r)

    for _ in range(n_queries):
        lines.append("qry")
        n_conds = rnd.randint(1, 4)
        for _ in range(n_conds):
            c = rnd.randrange(n_cols)
            kind = rnd.choice(["ge", "le", "eq", "ne", "nn", "nu"])
            if kind in ("nn", "nu"):
                lines.append("prd %s %d" % (kind, c))
            else:
                v = rnd.randint(-25, 25)
                lines.append("prd %s %d %d" % (kind, c, v))
        n_proj = rnd.randint(1, 3)
        proj_cols = [rnd.randrange(n_cols) for _ in range(n_proj)]
        lines.append("prj " + " ".join(str(x) for x in proj_cols))
        lines.append("end")

    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    seed = int(sys.argv[1])
    text = gen(seed)
    sys.stdout.write(text)
