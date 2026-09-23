import sys
import time

sys.path.insert(0, "/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p5_1b/app")

from scn import parse, rd, emit
import run_scan


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


def brute(seg, queries):
    cols_cache = {}

    def col(c):
        if c not in cols_cache:
            cols_cache[c] = build_column(seg, c)
        return cols_cache[c]

    out = []
    for q in queries:
        alive = [r for r in range(seg.n) if r not in seg.gone]
        for cond in q.conds:
            cv = col(cond.c)
            alive = [r for r in alive if rd.sat(cond, cv[r])]
        alive.sort()
        h = emit.digest(alive)
        out.append(("sel", len(alive), h))
        for c in q.cols:
            cv = col(c)
            nn = 0
            tot = 0
            for r in alive:
                v = cv[r]
                if v is not None:
                    nn += 1
                    tot += v
            out.append(("prj", c, nn, tot))
    return out


def extract(lines):
    out = []
    for ln in lines:
        f = ln.split()
        if f[0] == "sel":
            out.append(("sel", int(f[1]), int(f[2])))
        elif f[0] == "prj":
            out.append(("prj", int(f[1]), int(f[2]), int(f[3])))
    return out


def check_reads(lines, seg):
    # sanity: no dc/rd printed twice for the same key; every dc/rd's indices valid
    seen_dc = set()
    seen_rd = set()
    for ln in lines:
        f = ln.split()
        if f[0] == "dc":
            key = tuple(f[1:4])
            assert key not in seen_dc, ("duplicate dc", key)
            seen_dc.add(key)
        elif f[0] == "rd":
            key = tuple(f[1:3])
            assert key not in seen_rd, ("duplicate rd", key)
            seen_rd.add(key)
    return len(seen_dc), len(seen_rd)


def main():
    path = sys.argv[1]
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    t0 = time.time()
    lines = run_scan.run(text)
    t1 = time.time()
    seg, queries = parse.load(text)
    got = extract(lines)
    want = brute(seg, queries)
    ndc, nrd = check_reads(lines, seg)
    ok = got == want
    print(path, "TIME=%.3fs" % (t1 - t0), "dc=%d rd=%d lines=%d" % (ndc, nrd, len(lines)), "MATCH" if ok else "MISMATCH")
    if not ok:
        for i, (g, w) in enumerate(zip(got, want)):
            if g != w:
                print("  first mismatch at", i, "got", g, "want", w)
                break
        if len(got) != len(want):
            print("  length differs: got", len(got), "want", len(want))


if __name__ == "__main__":
    main()
