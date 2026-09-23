import random


def gen(seed, n=None, k=None):
    rnd = random.Random(seed)
    g = rnd.choice([1, 2, 3, 5, 10])
    n = n if n is not None else rnd.randint(6, 40)
    k = k if k is not None else rnd.randint(1, 4)
    lines = [f"seg {g} {n} {k}"]

    for c in range(k):
        pos = 0
        while pos < n:
            csize = rnd.randint(1, max(1, (n - pos) // rnd.randint(1, 3) + 1))
            csize = min(csize, n - pos)
            csize = max(csize, 1)
            enc = rnd.choice(["p", "p", "d"])
            dic = None
            if enc == "d":
                m = rnd.randint(1, 5)
                vals = sorted(rnd.sample(range(-20, 60), m))
                dic = vals

            # Build pages for this chunk first (need values to know sum).
            ppos = 0
            pages = []
            while ppos < csize:
                psize = rnd.randint(1, max(1, (csize - ppos) // rnd.randint(1, 2) + 1))
                psize = min(psize, csize - ppos)
                psize = max(psize, 1)
                nulls_n = rnd.randint(0, psize) if rnd.random() < 0.4 else 0
                nn_idx = set(rnd.sample(range(psize), nulls_n)) if nulls_n else set()
                form = "v"
                if enc == "d" and rnd.random() < 0.6:
                    form = "i"
                rowvals = []
                for i in range(psize):
                    if i in nn_idx:
                        rowvals.append(None)
                    else:
                        if form == "i":
                            idx = rnd.randrange(len(dic))
                            rowvals.append(dic[idx])
                        else:
                            if enc == "d" and rnd.random() < 0.3:
                                rowvals.append(rnd.choice(dic))
                            else:
                                rowvals.append(rnd.randint(-20, 60))
                pages.append((psize, nulls_n, nn_idx, form, rowvals))
                ppos += psize

            chunk_sum = sum(v for (_, _, _, _, rv) in pages for v in rv if v is not None)
            if enc == "p":
                lines.append(f"ch {c} p {chunk_sum}")
            else:
                lines.append(f"ch {c} d {chunk_sum} {len(dic)} " + " ".join(str(x) for x in dic))

            for (psize, nulls_n, nn_idx, form, rowvals) in pages:
                nonnull = [v for v in rowvals if v is not None]
                if nonnull:
                    true_lo = min(nonnull)
                    true_hi = max(nonnull)
                else:
                    true_lo = true_hi = None
                if true_lo is None:
                    mn_s, mx_s = "-", "-"
                    x = rnd.choice(["e", "w"])
                else:
                    x = rnd.choice(["e", "w"])
                    mn_s, mx_s = str(true_lo), str(true_hi)
                if form == "i":
                    toks = []
                    for v in rowvals:
                        if v is None:
                            toks.append("-")
                        else:
                            toks.append(str(dic.index(v)))
                else:
                    toks = [("-" if v is None else str(v)) for v in rowvals]
                lines.append(
                    f"pg {psize} {nulls_n} {mn_s} {mx_s} {x} {form} " + " ".join(toks)
                )
            pos += csize

    # updates
    used = set()
    nup = rnd.randint(0, n)
    for _ in range(nup):
        c = rnd.randrange(k)
        r = rnd.randrange(n)
        if (c, r) in used:
            continue
        used.add((c, r))
        if rnd.random() < 0.2:
            lines.append(f"up {c} {r} -")
        else:
            lines.append(f"up {c} {r} {rnd.randint(-20, 60)}")

    # deletes
    ndel = rnd.randint(0, max(0, n // 3))
    dels = rnd.sample(range(n), min(ndel, n))
    for r in dels:
        lines.append(f"del {r}")

    nq = rnd.randint(1, 3)
    for _ in range(nq):
        lines.append("qry")
        nc = rnd.randint(1, 4)
        for _ in range(nc):
            kind = rnd.choice(["ge", "le", "eq", "ne", "nn", "nu"])
            c = rnd.randrange(k)
            if kind in ("nn", "nu"):
                lines.append(f"prd {kind} {c}")
            else:
                v = rnd.randint(-25, 65)
                lines.append(f"prd {kind} {c} {v}")
        # one or more prj lines, with possible repeats
        nprj_lines = rnd.randint(1, 2)
        for _ in range(nprj_lines):
            ncols = rnd.randint(1, 3)
            cols = [rnd.randrange(k) for _ in range(ncols)]
            lines.append("prj " + " ".join(str(x) for x in cols))
        lines.append("end")

    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    import sys

    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    sys.stdout.write(gen(seed))
