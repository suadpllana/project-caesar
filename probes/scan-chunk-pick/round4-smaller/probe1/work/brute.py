import sys

sys.path.insert(0, "/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p5_1b/app")

from scn import parse, rd, emit


def row_value(seg, c, r):
    up = seg.up[c]
    if r in up:
        return up[r]
    for ch in seg.cols[c]:
        if ch.start <= r < ch.start + ch.n:
            for pg in ch.pages:
                if pg.start <= r < pg.start + pg.n:
                    i = r - pg.start
                    tok = pg.toks[i]
                    if tok is None:
                        return None
                    if pg.form == "v":
                        return tok
                    return ch.dic[tok]
    raise KeyError(r)


def brute(seg, q):
    alive = [r for r in range(seg.n) if r not in seg.gone]
    for cond in q.conds:
        alive = [r for r in alive if rd.sat(cond, row_value(seg, cond.c, r))]
    alive.sort()
    sel = (len(alive), emit.digest(alive))
    prjs = []
    for c in q.cols:
        nn = 0
        tot = 0
        for r in alive:
            v = row_value(seg, c, r)
            if v is not None:
                nn += 1
                tot += v
        prjs.append((c, nn, tot))
    return sel, prjs


def main():
    path = sys.argv[1]
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    seg, queries = parse.load(text)
    for i, q in enumerate(queries):
        sel, prjs = brute(seg, q)
        print("qry", i, "sel", sel[0], sel[1])
        for c, nn, tot in prjs:
            print(" prj", c, nn, tot)


if __name__ == "__main__":
    main()
