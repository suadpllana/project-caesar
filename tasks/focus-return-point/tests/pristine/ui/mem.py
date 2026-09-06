from ui import reach


def note(mem, nd):
    c = reach.within(nd)
    if c is not None:
        mem[c] = nd


def enter(ui, mem, comp, d=1):
    room = reach.inside(ui, comp)
    if not room:
        return None
    if d < 0:
        return room[-1]
    m = mem.get(comp)
    if m is not None and m in room:
        return m
    return room[0]
