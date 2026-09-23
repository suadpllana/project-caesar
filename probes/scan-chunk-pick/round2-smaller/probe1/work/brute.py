import sys

sys.path.insert(0, "/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p6_1/app")

from scn import parse, rd

MOD = 2305843009213693951


def digest(rows):
    h = 0
    for r in rows:
        h = (h * 1000003 + r + 1) % MOD
    return h


def effective_value(seg, c, r):
    up = seg.up[c]
    if r in up:
        return up[r]
    for ch in seg.cols[c]:
        if ch.start <= r < ch.start + ch.n:
            vals = rd.values(ch)
            return vals[r - ch.start]
    raise AssertionError("row not covered by any chunk: col=%d row=%d" % (c, r))


def run(text):
    seg, queries = parse.load(text)
    out_lines = []
    for qi, q in enumerate(queries):
        out_lines.append("qry %d" % qi)
        alive = [r for r in range(seg.n) if r not in seg.gone]
        for cd in q.conds:
            new_alive = []
            for r in alive:
                v = effective_value(seg, cd.c, r)
                if rd.sat(cd, v):
                    new_alive.append(r)
            alive = new_alive
        out_lines.append("sel %d %d" % (len(alive), digest(alive)))
        for c in q.cols:
            nn = 0
            tot = 0
            for r in alive:
                v = effective_value(seg, c, r)
                if v is not None:
                    nn += 1
                    tot += v
            out_lines.append("prj %d %d %d" % (c, nn, tot))
    return out_lines


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as fh:
        text = fh.read()
    print("\n".join(run(text)))
