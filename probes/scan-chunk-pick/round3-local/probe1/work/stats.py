import sys, collections
sys.path.insert(0, '../app')
from scn import parse
for fn in sys.argv[1:]:
    seg, qs = parse.load(open(fn).read())
    c = collections.Counter()
    for col in seg.cols:
        for ch in col:
            c['chunks'] += 1
            c['enc_' + ch.enc] += 1
            if ch.enc == 'd':
                c['dic_len_%s' % ('1' if len(ch.dic) == 1 else ('0' if not ch.dic else 'many'))] += 1
            for pg in ch.pages:
                c['pages'] += 1
                c['form_' + pg.form + '_in_' + ch.enc] += 1
                c['exact' if pg.exact else 'wide'] += 1
                if pg.mn is None:
                    c['allnull'] += 1
                    assert pg.nulls == pg.n
                else:
                    if pg.mn > pg.mx: c['mn>mx_' + ('e' if pg.exact else 'w')] += 1
                    if pg.mn == pg.mx: c['mn==mx_' + ('e' if pg.exact else 'w')] += 1
                    if pg.nulls == 0: c['nonull'] += 1
                # verify header consistency
                vals = [None if t is None else (t if pg.form == 'v' else ch.dic[t]) for t in pg.toks]
                nn = [v for v in vals if v is not None]
                assert len(vals) == pg.n
                assert pg.n - len(nn) == pg.nulls, (fn, pg.c, pg.j, pg.p)
                assert sum(nn) == pg.sum
                if nn:
                    lo, hi = (pg.mn, pg.mx) if pg.exact else (pg.mn - seg.g + 1, pg.mx + seg.g - 1)
                    assert lo <= min(nn) and max(nn) <= hi, (fn, pg.c, pg.j, pg.p)
                    if pg.exact and (lo != min(nn) or hi != max(nn)): c['e_loose'] += 1
                    if not pg.exact and seg.g > 1:
                        import math
                        if pg.mn != -(-min(nn)//seg.g)*seg.g or pg.mx != (max(nn)//seg.g)*seg.g: c['w_nonround'] += 1
    c['rows'] = seg.n
    c['cols'] = seg.k
    c['G'] = seg.g
    c['ups'] = sum(len(u) for u in seg.up)
    c['dels'] = len(seg.gone)
    c['queries'] = len(qs)
    print(fn, dict(sorted(c.items())))
