from tab import live, mark


def part(tab, base, buck, lo, hi):
    reach = []
    for s in live.inside(tab, buck, lo, hi):
        if s.born <= base:
            reach.append(s)
    if not reach:
        return False
    mark.keep(tab, buck, reach)
    return True
