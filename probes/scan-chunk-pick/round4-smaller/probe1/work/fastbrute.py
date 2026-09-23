import sys

sys.path.insert(0, "/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p5_1b/app")

from scn import parse, rd, emit


def build_column(seg, c):
    vals = [None] * seg.n
    for ch in seg.cols[c]:
        for pg in ch.pages:
            base = pg.start
            for i, tok in enumerate(pg.toks):
                if tok is None:
                    v = None
                elif pg.form == "v":
                    v = tok
                else:
                    v = ch.dic[tok]
                vals[base + i] = v
    for r, v in seg.up[c].items():
        vals[r] = v
    return vals


def main():
    path = sys.argv[1]
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    seg, queries = parse.load(text)
    cols_cache = {}

    def col(c):
        if c not in cols_cache:
            cols_cache[c] = build_column(seg, c)
        return cols_cache[c]

    for i, q in enumerate(queries):
        alive = [r for r in range(seg.n) if r not in seg.gone]
        for cond in q.conds:
            cv = col(cond.c)
            alive = [r for r in alive if rd.sat(cond, cv[r])]
        alive.sort()
        h = emit.digest(alive)
        print("qry", i, "sel", len(alive), h)
        for c in q.cols:
            cv = col(c)
            nn = 0
            tot = 0
            for r in alive:
                v = cv[r]
                if v is not None:
                    nn += 1
                    tot += v
            print(" prj", c, nn, tot)


if __name__ == "__main__":
    main()
