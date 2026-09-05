from ui import reach


def note(mem, nd):
    c = reach.within(nd)
    if c is not None:
        mem[c] = nd


def enter(ui, mem, comp):
    m = mem.get(comp)
    if m is not None and reach.within(m) is comp and reach.can(ui, m):
        return m
    room = reach.inside(ui, comp)
    return room[0] if room else None
