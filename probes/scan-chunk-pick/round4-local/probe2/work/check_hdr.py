import sys, collections
sys.path.insert(0, 'app')
from scn import parse, rd
for fn in sys.argv[1:]:
    seg, qs = parse.load(open(fn).read())
    G = seg.g
    bad = collections.Counter()
    for c in range(seg.k):
        for ch in seg.cols[c]:
            s = 0
            for pg in ch.pages:
                vals = rd.values(ch, pg)
                nn = [v for v in vals if v is not None]
                s += sum(nn)
                if len(vals) != pg.n: bad['len'] += 1
                if pg.n - len(nn) != pg.nulls: bad['nulls'] += 1
                if pg.mn is None:
                    if nn: bad['nobounds_but_values'] += 1
                    continue
                if not nn: bad['bounds_but_allnull'] += 1; continue
                if pg.mn > pg.mx: bad['inverted'] += 1
                lo, hi = (pg.mn, pg.mx) if pg.exact else (pg.mn - G + 1, pg.mx + G - 1)
                if min(nn) < lo or max(nn) > hi: bad['outside'] += 1
                if pg.exact and (min(nn) != pg.mn or max(nn) != pg.mx): bad['exact_not_tight'] += 1
                if not pg.exact:
                    tl = -(-min(nn) // G) * G
                    th = (max(nn) // G) * G
                    if (tl, th) != (pg.mn, pg.mx): bad['w_not_rounded_inward'] += 1
                if pg.form == 'i' and ch.dic is None: bad['i_no_dic'] += 1
            if s != ch.sum: bad['sum'] += 1
            if ch.dic is not None and sorted(set(ch.dic)) != ch.dic: bad['dic_not_sorted_unique'] += 1
    print(fn, dict(bad), 'n pages', sum(len(ch.pages) for c in range(seg.k) for ch in seg.cols[c]))
