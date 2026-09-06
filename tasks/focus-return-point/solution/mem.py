"""Remember branches, updating each enclosing scope on every landing."""
from ui import reach


def note(mem, nd):
    branch = nd
    c = reach.within(branch) if branch is not None else None
    while c is not None:
        mem[c] = branch
        branch = c
        c = reach.within(c)


def enter(ui, mem, comp):
    while comp is not None:
        m = mem.get(comp)
        valid = m is not None and reach.alive(ui, m) and reach.within(m) is comp
        if valid:
            valid = bool(reach.inside(ui, m)) if "comp" in m.fl else reach.can(ui, m)
        if not valid:
            room = reach.stops(ui, comp)
            m = room[0] if room else None
        if m is None or "comp" not in m.fl:
            return m
        comp = m
