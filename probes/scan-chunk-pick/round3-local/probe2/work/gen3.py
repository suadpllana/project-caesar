"""gen.py files with some page headers made untrue of their values."""
import random

import gen


def make(seed):
    rng = random.Random(seed ^ 0x5EED)
    out = []
    for line in gen.make(seed).split("\n"):
        f = line.split()
        if f and f[0] == "pg" and f[3] != "-" and rng.random() < 0.3:
            n, u = int(f[1]), int(f[2])
            mn, mx = int(f[3]), int(f[4])
            what = rng.randrange(3)
            if what == 0:
                if rng.random() < 0.5:
                    mn += rng.randint(1, 6)
                else:
                    mx -= rng.randint(1, 6)
            elif what == 1 and n > 1:
                u = min(n - 1, max(0, u + rng.choice([-1, 1])))
            else:
                f[6] = str(int(f[6]) + rng.randint(-9, 9))
            g = int(gen.make(seed).split("\n", 1)[0].split()[1])
            w = 0 if f[5] == "e" else g - 1
            if mn - w > mx + w:
                mn, mx = int(f[3]), int(f[4])
            f[2], f[3], f[4] = str(u), str(mn), str(mx)
            line = " ".join(f)
        out.append(line)
    return "\n".join(out)
