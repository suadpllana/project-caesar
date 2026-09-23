"""Wide-shaped random segment files (many small chunks), at a scale the model can check."""
import random


def gen(seed, N=1200, K=5, chunk=(16, 40), page=(4, 12), nq=3, nc=8):
    R = random.Random(seed)
    G = R.choice([25, 10, 5, 1])
    lines = ['seg %d %d %d' % (G, N, K)]
    ranges = []
    for c in range(K):
        if R.random() < 0.3:
            ranges.append((0, 39))
        else:
            base = R.choice([0, 300, -50])
            ranges.append((base, base + R.choice([40, 200, 400])))
    for c in range(K):
        vlo, vhi = ranges[c]
        r = 0
        while r < N:
            cn = R.randint(*chunk)
            if N - r < cn + chunk[0]:
                cn = N - r
            enc = 'd' if R.random() < 0.3 else 'p'
            dic = None
            if enc == 'd':
                m = R.choice([1, 1, 3, 6, 12, 20])
                span = R.randint(0, vhi - vlo)
                a = R.randint(vlo, vhi - span)
                pool = list(range(a, a + span + 1))
                dic = sorted(R.sample(pool, min(m, len(pool))))
            pages = []
            left = cn
            while left > 0:
                pn = R.randint(*page)
                if left < pn + page[0]:
                    pn = left
                left -= pn
                form = 'i' if (enc == 'd' and R.random() < 0.8) else 'v'
                nullp = R.choice([0, 0, 0, 0.1, 0.3, 1.0])
                constv = R.random() < 0.1
                if form == 'i':
                    cv = R.choice(dic)
                else:
                    cv = R.randint(vlo, vhi)
                plo = R.randint(vlo, vhi)
                phi = min(vhi, plo + R.choice([5, 30, 100, 400]))
                vals = []
                for _ in range(pn):
                    if R.random() < nullp:
                        vals.append(None)
                    elif constv:
                        vals.append(cv)
                    elif form == 'i':
                        vals.append(R.choice(dic))
                    else:
                        vals.append(R.randint(plo, phi))
                nn = [x for x in vals if x is not None]
                u = pn - len(nn)
                if not nn:
                    mn = mx = '-'
                    x = 'e'
                else:
                    x = R.choice('ew')
                    tl = -(-min(nn) // G) * G
                    th = (max(nn) // G) * G
                    if x == 'w' and tl <= th:
                        mn, mx = tl, th
                    else:
                        x = 'e'
                        mn, mx = min(nn), max(nn)
                if form == 'i':
                    toks = ['-' if v is None else str(dic.index(v)) for v in vals]
                else:
                    toks = ['-' if v is None else str(v) for v in vals]
                pages.append((pn, u, mn, mx, x, form, toks, sum(nn)))
            s = sum(p[7] for p in pages)
            if enc == 'd':
                lines.append('ch %d d %d %d %s' % (c, s, len(dic), ' '.join(map(str, dic))))
            else:
                lines.append('ch %d p %d' % (c, s))
            for (pn, u, mn, mx, x, form, toks, _) in pages:
                lines.append('pg %d %d %s %s %s %s %s' % (pn, u, mn, mx, x, form, ' '.join(toks)))
            r += cn
    seen = set()
    for _ in range(N * K // 20):
        c = R.randrange(K)
        r = R.randrange(N)
        if (c, r) in seen:
            continue
        seen.add((c, r))
        vlo, vhi = ranges[c]
        v = '-' if R.random() < 0.2 else str(R.randint(vlo, vhi))
        lines.append('up %d %d %s' % (c, r, v))
    for r in sorted(set(R.randrange(N) for _ in range(N // 100 + 1))):
        lines.append('del %d' % r)
    for _ in range(nq):
        lines.append('qry')
        for _ in range(nc):
            kind = R.choice(['ge', 'le', 'ne', 'nn', 'nn', 'nn', 'ge', 'le', 'ne', 'eq', 'nu'])
            c = R.randrange(K)
            vlo, vhi = ranges[c]
            w = vhi - vlo
            if kind in ('nn', 'nu'):
                lines.append('prd %s %d' % (kind, c))
            else:
                if kind == 'ge':
                    v = vlo + R.randint(0, w // 3)
                elif kind == 'le':
                    v = vhi - R.randint(0, w // 3)
                else:
                    v = R.randint(vlo, vhi)
                lines.append('prd %s %d %d' % (kind, c, v))
        cols = [R.randrange(K) for _ in range(R.randint(1, 3))]
        lines.append('prj ' + ' '.join(map(str, cols)))
        lines.append('end')
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    import sys
    sys.stdout.write(gen(int(sys.argv[1])))
