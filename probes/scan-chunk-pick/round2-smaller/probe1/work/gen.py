import random
import sys


def gen_seg(rng, n_rows_max=40, n_cols=3, g=None):
    g = g if g is not None else rng.choice([1, 2, 3, 5, 10])
    n = rng.randint(1, n_rows_max)
    k = n_cols
    lines = []
    col_ranges = [[] for _ in range(k)]  # list of (start, n) per column, for building own map
    col_true_vals = [[None] * n for _ in range(k)]  # true per-row raw (pre-update) value, for reference

    for c in range(k):
        pos = 0
        chunk_idx = 0
        while pos < n:
            remaining = n - pos
            clen = rng.randint(1, min(6, remaining))
            pos_end = pos + clen
            # decide nulls
            nulls = rng.randint(0, clen)
            null_positions = set(rng.sample(range(clen), nulls))
            vlo = rng.randint(-20, 20)
            vhi = vlo + rng.randint(0, 40)
            raw_vals = []
            for i in range(clen):
                if i in null_positions:
                    raw_vals.append(None)
                else:
                    raw_vals.append(rng.randint(vlo, vhi))
            non_null = [v for v in raw_vals if v is not None]
            if non_null:
                true_mn = min(non_null)
                true_mx = max(non_null)
            else:
                true_mn = None
                true_mx = None

            exact = rng.random() < 0.5
            enc = rng.random() < 0.45  # True => dict

            if true_mn is None:
                mn_tok, mx_tok = "-", "-"
                xtok = "e"
            else:
                if exact:
                    mn_tok, mx_tok = str(true_mn), str(true_mx)
                    xtok = "e"
                else:
                    # round outward-from-truth i.e. inward on the interval:
                    # recorded_lo = smallest multiple of g >= true_mn
                    # recorded_hi = largest multiple of g <= true_mx
                    rec_lo = -(-true_mn // g) * g if g > 0 else true_mn
                    rec_hi = (true_mx // g) * g if g > 0 else true_mx
                    mn_tok, mx_tok = str(rec_lo), str(rec_hi)
                    xtok = "w"

            if enc:
                # dictionary encoding
                distinct = sorted(set(non_null))
                star_positions = set()
                # occasionally force a couple of values out as '*' literals
                if distinct and rng.random() < 0.35:
                    cand = [i for i in range(clen) if raw_vals[i] is not None]
                    if cand:
                        star_positions = set(rng.sample(cand, rng.randint(1, min(2, len(cand)))))
                dict_vals = sorted(set(v for i, v in enumerate(raw_vals)
                                        if v is not None and i not in star_positions))
                if not dict_vals and distinct:
                    # ensure a non-empty dict when possible by not starring everything
                    star_positions = set()
                    dict_vals = distinct
                tokens = []
                for i, v in enumerate(raw_vals):
                    if v is None:
                        tokens.append("-")
                    elif i in star_positions:
                        tokens.append("*%d" % v)
                    else:
                        tokens.append(str(dict_vals.index(v)))
                line = "ch %d %d %d %s %s %s d %d %s %s" % (
                    c, clen, nulls, mn_tok, mx_tok, xtok, len(dict_vals),
                    " ".join(str(x) for x in dict_vals), " ".join(tokens),
                )
            else:
                tokens = ["-" if v is None else str(v) for v in raw_vals]
                line = "ch %d %d %d %s %s %s p %s" % (
                    c, clen, nulls, mn_tok, mx_tok, xtok, " ".join(tokens),
                )
            lines.append(line)
            for i, v in enumerate(raw_vals):
                col_true_vals[c][pos + i] = v
            col_ranges[c].append((pos, clen))
            pos = pos_end
            chunk_idx += 1

    # updates
    updates = [dict() for _ in range(k)]
    n_updates = rng.randint(0, n)
    for _ in range(n_updates):
        c = rng.randrange(k)
        r = rng.randrange(n)
        if r in updates[c]:
            continue
        if rng.random() < 0.15:
            v = None
        else:
            v = rng.randint(-30, 30)
        updates[c][r] = v
        lines.append("up %d %d %s" % (c, r, "-" if v is None else str(v)))

    # deletes
    gone = set()
    n_del = rng.randint(0, max(0, n // 3))
    for r in rng.sample(range(n), min(n_del, n)):
        gone.add(r)
        lines.append("del %d" % r)

    header = "seg %d %d %d" % (g, n, k)
    return header, lines, n, k, col_true_vals, updates, gone


def gen_query(rng, n, k, qidx):
    lines = ["qry"]
    n_conds = rng.randint(1, 4)
    kinds = ["ge", "le", "eq", "ne", "nn", "nu"]
    for _ in range(n_conds):
        c = rng.randrange(k)
        kind = rng.choice(kinds)
        if kind in ("nn", "nu"):
            lines.append("prd %s %d" % (kind, c))
        else:
            v = rng.randint(-25, 25)
            lines.append("prd %s %d %d" % (kind, c, v))
    n_proj = rng.randint(1, 4)
    proj_cols = [rng.randrange(k) for _ in range(n_proj)]
    lines.append("prj " + " ".join(str(x) for x in proj_cols))
    lines.append("end")
    return lines


def gen_file(seed, n_rows_max=40, n_cols=3, n_queries=3):
    rng = random.Random(seed)
    header, seg_lines, n, k, col_true_vals, updates, gone = gen_seg(rng, n_rows_max, n_cols)
    lines = [header] + seg_lines
    for i in range(n_queries):
        lines.extend(gen_query(rng, n, k, i))
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    sys.stdout.write(gen_file(seed))
