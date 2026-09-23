import sys, collections
sys.path.insert(0, 'app')
from scn import parse, hdr
for fn in sys.argv[1:]:
    seg, qs = parse.load(open(fn).read())
    diff = collections.Counter()
    for qi, q in enumerate(qs):
        for cd in q.conds:
            if cd.kind not in hdr.COMPARE: continue
            t = hdr.test(cd.kind, cd.v)
            for ch in seg.cols[cd.c]:
                if ch.dic is None: continue
                good = sum(1 for e in ch.dic if t(e))
                for pg in ch.pages:
                    if pg.form != 'i': continue
                    lo, hi = hdr.bounds(seg.g, pg)
                    hv = hdr.verdict(cd.kind, cd.v, pg.n, pg.nulls, lo, hi)
                    if hv: continue
                    dv = -1 if good == 0 else (1 if good == len(ch.dic) and pg.nulls == 0 else 0)
                    ins = [e for e in ch.dic if lo is not None and lo <= e <= hi]
                    g2 = sum(1 for e in ins if t(e))
                    iv = -1 if g2 == 0 else (1 if g2 == len(ins) and pg.nulls == 0 else 0)
                    if iv != dv:
                        diff[(qi, cd.kind, dv, iv)] += 1
    print(fn, dict(diff))
