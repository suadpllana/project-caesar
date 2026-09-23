import sys, random
sys.path.insert(0, '/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p4_2/app')
from scn import hdr
R = random.Random(1)
for trial in range(20000):
    n = R.randint(0, 12)
    u = R.randint(0, n)
    if u == n and R.random() < 0.9:
        lo = hi = None
    else:
        lo = R.randint(-20, 20)
        hi = lo + R.randint(0, 25)
    kind = R.choice(['ge', 'le', 'eq', 'ne', 'nn', 'nu'])
    v = R.randint(-30, 50)
    a = hdr.verdict(kind, v, n, u, lo, hi)
    b = hdr.verdicts(kind, v, [n], [u], [lo], [hi])[0]
    assert a == b, (kind, v, n, u, lo, hi, a, b)
    a = hdr.spread(kind, v, n, u, lo, hi)
    b = hdr.spreads(kind, v, [n], [u], [lo], [hi])[0]
    assert a == b, ('spread', kind, v, n, u, lo, hi, a, b)
print('vectorized helpers agree')
