"""Random small segment files exercising every feature the brief names."""
import random


def gen(seed):
    R = random.Random(seed)
    G = R.choice([1, 1, 2, 3, 5, 10])
    N = R.randint(20, 90)
    K = R.randint(1, 4)
    lines = ['seg %d %d %d' % (G, N, K)]
    maxchunk = R.choice([3, 6, 12, 40])
    maxpage = R.choice([1, 2, 3, 6])
    vlo = R.choice([0, -10, 0, 5])
    vhi = vlo + R.choice([1, 3, 8, 20, 60])
    for c in range(K):
        r = 0
        while r < N:
            cn = min(N - r, R.randint(1, maxchunk))
            enc = R.choice(['p', 'd', 'd'])
            dic = None
            if enc == 'd':
                m = R.choice([1, 1, 2, 3, 5])
                dic = sorted(R.sample(range(vlo, vhi + 1), min(m, vhi - vlo + 1)))
            pages = []
            left = cn
            while left > 0:
                pn = min(left, R.randint(1, maxpage))
                left -= pn
                form = 'i' if (enc == 'd' and R.random() < 0.75) else 'v'
                nullp = R.choice([0, 0, 0.3, 0.6, 1.0])
                constv = R.random() < 0.2
                cv = R.randint(vlo, vhi) if form == 'v' else R.choice(dic)
                vals = []
                for _ in range(pn):
                    if R.random() < nullp:
                        vals.append(None)
                    elif constv:
                        vals.append(cv)
                    elif form == 'i':
                        vals.append(R.choice(dic))
                    else:
                        vals.append(R.randint(vlo, vhi))
                nn = [x for x in vals if x is not None]
                u = pn - len(nn)
                if not nn:
                    mn = mx = '-'
                    x = R.choice('ew')
                else:
                    x = R.choice('ew')
                    if x == 'e':
                        mn, mx = min(nn), max(nn)
                    else:
                        mn = -(-min(nn) // G) * G
                        mx = (max(nn) // G) * G
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
    # updates
    seen = set()
    for _ in range(R.choice([0, 1, 3, N // 2 + 1])):
        c = R.randrange(K)
        r = R.randrange(N)
        if (c, r) in seen:
            continue
        seen.add((c, r))
        v = '-' if R.random() < 0.25 else str(R.randint(vlo - 2, vhi + 2))
        lines.append('up %d %d %s' % (c, r, v))
    dels = set()
    for _ in range(R.choice([0, 1, 2, N // 4 + 1])):
        dels.add(R.randrange(N))
    for r in sorted(dels):
        lines.append('del %d' % r)
    for _ in range(R.randint(2, 6)):
        lines.append('qry')
        for _ in range(R.randint(1, 8)):
            kind = R.choice(['ge', 'le', 'eq', 'ne', 'nn', 'nu', 'ge', 'le', 'eq', 'ne'])
            c = R.randrange(K)
            if kind in ('nn', 'nu'):
                lines.append('prd %s %d' % (kind, c))
            else:
                lines.append('prd %s %d %d' % (kind, c, R.randint(vlo - 3, vhi + 3)))
        cols = [R.randrange(K) for _ in range(R.randint(1, 3))]
        lines.append('prj ' + ' '.join(map(str, cols)))
        lines.append('end')
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    import sys
    sys.stdout.write(gen(int(sys.argv[1])))
