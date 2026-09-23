import random
import sys

sys.path.insert(0, "/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p6_1/work")
import gen as base


def gen_seg_tight(rng, n_rows_max=30, n_cols=2, g=None):
    # monkeypatch value range to be tiny so single-value / collapsed-bounds
    # chunks, and dictionaries with repeated entries, are common.
    orig_randint = rng.randint

    def tiny_randint(a, b):
        if (a, b) == (-20, 20):
            return orig_randint(-2, 2)
        if (a, b) == (-25, 25):
            return orig_randint(-3, 3)
        if (a, b) == (-30, 30):
            return orig_randint(-3, 3)
        return orig_randint(a, b)

    rng.randint = tiny_randint
    try:
        return base.gen_seg(rng, n_rows_max, n_cols, g)
    finally:
        rng.randint = orig_randint


def gen_query_focused(rng, n, k, qidx):
    lines = ["qry"]
    n_conds = rng.randint(2, 6)
    kinds = ["ge", "le", "eq", "ne", "nn", "nu"]
    # concentrate on 1-2 columns to force multiple conditions per column
    hot_cols = [rng.randrange(k) for _ in range(rng.randint(1, min(2, k)))]
    for _ in range(n_conds):
        c = rng.choice(hot_cols) if rng.random() < 0.75 else rng.randrange(k)
        kind = rng.choice(kinds)
        if kind in ("nn", "nu"):
            lines.append("prd %s %d" % (kind, c))
        else:
            v = rng.randint(-3, 3)
            lines.append("prd %s %d %d" % (kind, c, v))
    n_proj = rng.randint(1, 5)
    proj_cols = [rng.randrange(k) for _ in range(n_proj)]
    lines.append("prj " + " ".join(str(x) for x in proj_cols))
    lines.append("end")
    return lines


def gen_file(seed, n_rows_max=30, n_cols=2, n_queries=4):
    rng = random.Random(seed)
    header, seg_lines, n, k, col_true_vals, updates, gone = gen_seg_tight(
        rng, n_rows_max, n_cols
    )
    lines = [header] + seg_lines
    for i in range(n_queries):
        lines.extend(gen_query_focused(rng, n, k, i))
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    sys.stdout.write(gen_file(seed))
