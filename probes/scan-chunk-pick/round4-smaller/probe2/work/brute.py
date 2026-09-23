import sys

sys.path.insert(0, "/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p5_2/app")

from scn import parse, rd, emit


def run(text):
    seg, queries = parse.load(text)
    colvals = []
    for c in range(seg.k):
        arr = [None] * seg.n
        for ch in seg.cols[c]:
            for pg in ch.pages:
                vals = rd.values(ch, pg)
                for i, v in enumerate(vals):
                    arr[pg.start + i] = v
        up = seg.up[c]
        for r, v in up.items():
            arr[r] = v
        colvals.append(arr)

    out_lines = []
    for qi, q in enumerate(queries):
        out_lines.append("qry %d" % qi)
        alive = set(range(seg.n)) - seg.gone
        for cd in q.conds:
            col = colvals[cd.c]
            alive = {r for r in alive if rd.sat(cd, col[r])}
        rows = sorted(alive)
        out_lines.append("sel %d %d" % (len(rows), emit.digest(rows)))
        for c in q.cols:
            col = colvals[c]
            nn = 0
            tot = 0
            for r in rows:
                v = col[r]
                if v is not None:
                    nn += 1
                    tot += v
            out_lines.append("prj %d %d %d" % (c, nn, tot))
    return out_lines


def main():
    with open(sys.argv[1], encoding="utf-8") as fh:
        text = fh.read()
    print("\n".join(run(text)))


if __name__ == "__main__":
    main()
