"""The forest: which still a line was grafted from, which line owns which still, and the lift.

A still records the line it was taken on, which never changes, and the line that owns it,
which a lift does change. The first decides whose chains answer what the still holds; the
second decides which line is holding the blocks it holds, and that is why a lift moves a
charge without a single block being written or released.

A lift takes the stills of the line above up to and including the origin - the prefix, in the
order they were taken - hands them to the graft, and swaps the two origins, so the line above
becomes a graft of the one that was grafted from it.
"""
from led import cell, hold


class Still:
    __slots__ = ("on", "owner", "idx")

    def __init__(self, on, idx):
        self.on = on
        self.owner = on
        self.idx = idx


def freeze(st, name, still):
    """Taking a still costs nothing: the line already holds everything its head holds."""
    kit = hold.kit(st)
    one = cell.line(st, name)
    st.stills[still] = Still(name, kit.g)
    one.taken.append(kit.g)
    one.stills.append(still)
    hold.recut(st, name)
    kit.g += 1


def sprout(st, still, name):
    cell.mkline(st, name)
    one = cell.line(st, name)
    one.origin = still
    for c, b in cell.held(st, still):
        cell.plant(st, name, c, b)
        hold.touch(st, b)


def rooted(st, still):
    for one in st.lines.values():
        if one.origin == still:
            return True
    return False


def lift(st, name):
    one = cell.line(st, name)
    if one.origin is None:
        return
    still = one.origin
    above = cell.line(st, st.stills[still].owner)
    cut = above.stills.index(still) + 1
    moved = above.stills[:cut]
    above.stills = above.stills[cut:]
    one.stills = moved + one.stills
    touched = set()
    for each in moved:
        rec = st.stills[each]
        rec.owner = name
        hold.shift(st, rec.on, rec.idx, name)
        touched.add(rec.on)
    one.origin = above.origin
    above.origin = still
    hold.sweep(st, touched)
