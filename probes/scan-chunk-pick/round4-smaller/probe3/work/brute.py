"""Independent, deliberately naive reference: decode every page directly (no
memoisation, no header tricks, no dictionary shortcuts) and evaluate each
query by brute force over full per-row values. Used only to cross-check the
final `sel`/`prj` numbers the real solver produces, not the print order.
"""
import sys

sys.path.insert(0, "/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p5_3/app")

from scn import parse, rd


MOD = 2305843009213693951


def digest(rows):
    h = 0
    for r in rows:
        h = (h * 1000003 + r + 1) % MOD
    return h


def col_values(seg, c):
    vals = [None] * seg.n
    for ch in seg.cols[c]:
        for pg in ch.pages:
            pv = rd.values(ch, pg)
            for i, v in enumerate(pv):
                vals[pg.start + i] = v
    up = seg.up[c]
    for r, v in up.items():
        vals[r] = v
    return vals


def run(text):
    seg, queries = parse.load(text)
    colvals = [col_values(seg, c) for c in range(seg.k)]
    out = []
    for qi, q in enumerate(queries):
        alive = [r for r in range(seg.n) if r not in seg.gone]
        for cd in q.conds:
            cv = colvals[cd.c]
            alive = [r for r in alive if rd.sat(cd, cv[r])]
        out.append(("sel", len(alive), digest(sorted(alive))))
        for c in q.cols:
            cv = colvals[c]
            nn = 0
            tot = 0
            for r in alive:
                v = cv[r]
                if v is not None:
                    nn += 1
                    tot += v
            out.append(("prj", c, nn, tot))
    return out


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as fh:
        text = fh.read()
    for line in run(text):
        print(line)
