import sys, collections
sys.path.insert(0, 'app')
from scn import parse
for fn in sys.argv[1:]:
    seg, qs = parse.load(open(fn).read())
    print('==', fn, 'G', seg.g, 'N', seg.n, 'K', seg.k, 'queries', len(qs))
    for c in range(seg.k):
        chs = seg.cols[c]
        encs = collections.Counter(ch.enc for ch in chs)
        forms = collections.Counter((ch.enc, pg.form, 'e' if pg.exact else 'w') for ch in chs for pg in ch.pages)
        dsz = collections.Counter(len(ch.dic) for ch in chs if ch.dic is not None)
        single = sum(1 for ch in chs for pg in ch.pages if pg.mn is not None and pg.mn == pg.mx)
        allnull = sum(1 for ch in chs for pg in ch.pages if pg.mn is None)
        nonull = sum(1 for ch in chs for pg in ch.pages if pg.nulls == 0)
        npg = sum(len(ch.pages) for ch in chs)
        print(' col', c, 'chunks', len(chs), 'pages', npg, dict(encs), dict(forms), 'dictsizes', dict(sorted(dsz.items())[:10]), 'singlebound', single, 'allnull', allnull, 'nonull', nonull, 'updates', len(seg.up[c]))
    print(' deleted', len(seg.gone))
    for q in qs:
        print(' q', [(cd.kind, cd.c, cd.v) for cd in q.conds], q.cols)
