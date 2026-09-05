"""What a composite remembers.

A composite is one tab stop, and entering it lands on the descendant that most recently
held focus - by any means: a key inside it, a request, a return from a screen. The shipped
mem.py only learned from the arrow keys, so a request that put focus on the third item was
forgotten the moment focus left, and Tab came back to the first. The other half of the
shipped defect was in focus.py: entering backwards landed on the last item instead of the
remembered one.

The memory is a reference, never a position. If the remembered widget has been dropped or
can no longer take focus, the landing falls to the first descendant that can.
"""

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
