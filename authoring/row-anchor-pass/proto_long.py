import random


def long_doc(rng, ng=200000, events=2500):
    vh = rng.choice([600, 800])
    cap = rng.choice([900, 1400])
    lines = ["cfg %d %d %d %d %d" % (vh, 2, 4, rng.choice([20, 40]), cap)]
    n = {}
    tops = []
    reach = 0
    for k in range(ng):
        hh = 10 + (k * 7) % 9
        lo = 8 + (k * 5) % 13
        hi = lo + (k * 11) % 23
        rows = (k * 13) % 5
        lines.append("g %d %d %d %d %d" % (k + 1, hh, lo, hi, rows))
        n[k + 1] = rows
        tops.append(reach)
        reach += hh + rows * 20
    where = 0
    for _ in range(events):
        pick = rng.random()
        if pick < 0.72:
            d = rng.randint(vh // 3, vh)
            where += d
            lines.append("scroll %d" % d)
        elif pick < 0.80:
            d = rng.randint(vh // 4, vh)
            where = max(0, where - d)
            lines.append("scroll %d" % -d)
        elif pick < 0.84:
            where = rng.randint(0, reach)
            lines.append("go %d" % where)
        elif pick < 0.86:
            lines.append("size %d" % rng.choice([500, 700, 900]))
        else:
            gi = max(1, min(ng, 1 + sum(1 for t in tops[:1] if t <= where)))
            # an edit a little below the reading position
            lo_g = max(1, min(ng, int(where / (reach / ng)) + rng.randint(-5, 40)))
            gid = lo_g
            if rng.random() < 0.5 or n[gid] == 0:
                k = rng.randint(1, 3)
                lines.append("ins %d %d %d" % (gid, rng.randint(0, n[gid]), k))
                n[gid] += k
            else:
                k = rng.randint(1, n[gid])
                lines.append("del %d %d %d" % (gid, rng.randint(0, n[gid] - k), k))
                n[gid] -= k
    return lines
