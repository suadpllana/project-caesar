"""Independent brute-force reference: computes only `sel` and `prj` lines
(final results), directly from the row-level semantics in the brief,
with no attempt to replicate the dc/rd trace or the pick order.  Used to
cross-check the optimized implementation's final numbers.
"""
import sys

sys.path.insert(0, "/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p6_3/app")

from scn import parse, rd

MOD = 2305843009213693951


def digest(rows):
    h = 0
    for r in rows:
        h = (h * 1000003 + r + 1) % MOD
    return h


def col_values(seg, c):
    """Return a list of length seg.n: the chunk's own written value for
    every row of column c (no update overlay)."""
    out = [None] * seg.n
    for ch in seg.cols[c]:
        vs = rd.values(ch)
        for i, v in enumerate(vs):
            out[ch.start + i] = v
    return out


def run(text):
    seg, queries = parse.load(text)
    written = [col_values(seg, c) for c in range(seg.k)]

    def value(c, r):
        if r in seg.up[c]:
            return seg.up[c][r]
        return written[c][r]

    lines = []
    for qi, q in enumerate(queries):
        lines.append("qry %d" % qi)
        alive = [r for r in range(seg.n) if r not in seg.gone]
        for cd in q.conds:
            alive = [r for r in alive if rd.sat(cd, value(cd.c, r))]
        lines.append("sel %d %d" % (len(alive), digest(alive)))
        for c in q.cols:
            nn = 0
            tot = 0
            for r in alive:
                v = value(c, r)
                if v is not None:
                    nn += 1
                    tot += v
            lines.append("prj %d %d %d" % (c, nn, tot))
    return lines


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as fh:
        text = fh.read()
    print("\n".join(run(text)))
