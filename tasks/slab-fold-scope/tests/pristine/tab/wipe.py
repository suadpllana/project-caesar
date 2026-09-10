from tab import live


def part(tab, buck, lo, hi):
    for s in live.over(tab, buck, lo, hi):
        runs = []
        for a, z in s.runs:
            if a < lo:
                runs.append([a, min(z, lo - 1)])
            if z > hi:
                runs.append([max(a, hi + 1), z])
        s.runs = runs
        if not runs:
            live.lose(tab, buck, s)
    return hi - lo + 1
