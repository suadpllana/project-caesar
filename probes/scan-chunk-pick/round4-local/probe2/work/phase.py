import sys, time
sys.path.insert(0, '.')
from scn import parse, live, pick, proj, emit
for fn in sys.argv[1:]:
    text = open(fn).read()
    best = None
    for rep in range(3):
        t0 = time.perf_counter()
        seg, qs = parse.load(text)
        t1 = time.perf_counter()
        mem = live.fresh(seg)
        t2 = time.perf_counter()
        ts = [0, 0, 0, 0]
        out = emit.Out()
        for i, q in enumerate(qs):
            a = time.perf_counter()
            st = live.start(seg, q, mem)
            b = time.perf_counter()
            pick.run(seg, q, st, out)
            c = time.perf_counter()
            rows = live.rows(st)
            out.sel(len(rows), emit.digest(rows))
            d = time.perf_counter()
            proj.run(seg, q, st, rows, out)
            e = time.perf_counter()
            ts[0] += b - a; ts[1] += c - b; ts[2] += d - c; ts[3] += e - d
        r = (t1 - t0, t2 - t1, *ts)
        if best is None or sum(r) < sum(best):
            best = r
    print(fn, 'parse %.3f fresh %.3f start %.3f pick %.3f rows %.3f proj %.3f | ours %.3f' % (*best, sum(best[1:])))
