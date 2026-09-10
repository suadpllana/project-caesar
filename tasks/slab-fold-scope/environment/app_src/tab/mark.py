from tab import live


def fresh(tab, buck, lo, hi, num):
    s = live.Slab(tab.mint(), num)
    s.runs = [[lo, hi]]
    live.join(tab, buck, s)
    return s


def keep(tab, buck, reach):
    born = reach[0].born
    runs = []
    for s in reach:
        if s.born < born:
            born = s.born
        runs.extend(s.runs)
        live.lose(tab, buck, s)
    runs.sort()
    s = live.Slab(tab.mint(), born)
    s.runs = runs
    live.join(tab, buck, s)
    return s
