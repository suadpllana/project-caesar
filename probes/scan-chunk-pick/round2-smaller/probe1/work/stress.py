import random
import sys

sys.path.insert(0, "/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p6_1/app")


def build(seed, n=60000, k=5, chunk_lo=10, chunk_hi=24, n_conds=8, hot_frac=0.9):
    rng = random.Random(seed)
    lines = ["seg 25 %d %d" % (n, k)]
    for c in range(k):
        pos = 0
        while pos < n:
            clen = min(rng.randint(chunk_lo, chunk_hi), n - pos)
            nulls = rng.randint(0, max(0, clen // 4))
            null_pos = set(rng.sample(range(clen), min(nulls, clen)))
            vlo = rng.randint(-50, 0)
            vhi = vlo + rng.randint(5, 80)
            vals = []
            for i in range(clen):
                if i in null_pos:
                    vals.append(None)
                else:
                    vals.append(rng.randint(vlo, vhi))
            nn = [v for v in vals if v is not None]
            if nn:
                mn, mx = min(nn), max(nn)
            else:
                mn, mx = None, None
            exact = rng.random() < 0.5
            enc_dict = rng.random() < 0.4
            g = 25
            if mn is None:
                mn_t, mx_t, xt = "-", "-", "e"
            elif exact:
                mn_t, mx_t, xt = str(mn), str(mx), "e"
            else:
                rl = -(-mn // g) * g
                rh = (mx // g) * g
                mn_t, mx_t, xt = str(rl), str(rh), "w"
            if enc_dict:
                distinct = sorted(set(nn))
                toks = []
                for v in vals:
                    if v is None:
                        toks.append("-")
                    else:
                        toks.append(str(distinct.index(v)))
                lines.append(
                    "ch %d %d %d %s %s %s d %d %s %s"
                    % (c, clen, len(null_pos), mn_t, mx_t, xt, len(distinct),
                       " ".join(map(str, distinct)), " ".join(toks))
                )
            else:
                toks = ["-" if v is None else str(v) for v in vals]
                lines.append(
                    "ch %d %d %d %s %s %s p %s"
                    % (c, clen, len(null_pos), mn_t, mx_t, xt, " ".join(toks))
                )
            pos += clen

    n_up = n // 4
    for _ in range(n_up):
        c = rng.randrange(k)
        r = rng.randrange(n)
        v = rng.randint(-50, 30) if rng.random() > 0.1 else None
        lines.append("up %d %d %s" % (c, r, "-" if v is None else str(v)))
    n_del = n // 100
    for r in rng.sample(range(n), n_del):
        lines.append("del %d" % r)

    # queries: most conditions concentrated on column 0 (hot column)
    for _ in range(2):
        lines.append("qry")
        for _ in range(n_conds):
            if rng.random() < hot_frac:
                c = 0
            else:
                c = rng.randrange(k)
            kind = rng.choice(["ge", "le", "eq", "ne", "nn", "nu"])
            if kind in ("nn", "nu"):
                lines.append("prd %s %d" % (kind, c))
            else:
                v = rng.randint(-50, 30)
                lines.append("prd %s %d %d" % (kind, c, v))
        lines.append("prj " + " ".join(str(x) for x in range(k)))
        lines.append("end")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    text = build(seed)
    sys.stderr.write("chunks/updates/dels built\n")
    import time
    import run_scan
    t0 = time.time()
    out = run_scan.run(text)
    t1 = time.time()
    sys.stderr.write("run time: %.3fs, lines=%d\n" % (t1 - t0, len(out)))
    print("\n".join(out[:10]))
