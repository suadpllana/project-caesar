"""Search a focused space for the shortest program separating one reading from the reference.

    python3 search.py <reading> [tries]
"""
import random
import sys

import emit
import lab

name = sys.argv[1]
tries = int(sys.argv[2]) if len(sys.argv) > 2 else 4000
for b in emit.READING_BUILDERS:
    b()
ref = lab.pane("solution")
alt = lab.tree(files=emit.BUILT[name])
rng = random.Random("search|" + name)
best = None
for t in range(tries):
    vh = rng.choice([10, 12, 15, 20, 25, 30])
    cap = rng.choice([1, 2, 3, 4])
    n = rng.randint(3, 9)
    prog = ["cfg %d 0 %d 10 %d" % (vh, rng.choice([2, 3]), cap), "g 1 5 6 14 %d" % n]
    for _ in range(rng.randint(2, 6)):
        pick = rng.random()
        if pick < 0.6:
            prog.append("go %d" % rng.choice(range(0, 5 + 10 * n, 5)))
        elif pick < 0.8 and n > 1:
            k = 1
            pos = rng.randint(0, n - 1)
            prog.append("del 1 %d %d" % (pos, k))
            n -= k
        else:
            k = rng.randint(1, 2)
            prog.append("ins 1 %d %d" % (rng.randint(0, n), k))
            n += k
    try:
        if ref(prog) != alt(prog):
            if best is None or len(prog) < len(best):
                best = prog
    except Exception:
        continue
print(best and "\n".join(best))
