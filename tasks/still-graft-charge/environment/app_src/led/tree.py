from led import cell, hold


class Still:
    __slots__ = ("owner", "held")

    def __init__(self, owner, held):
        self.owner = owner
        self.held = held


def freeze(st, name, still):
    one = cell.line(st, name)
    held = cell.copy(st, name)
    for b in held.values():
        hold.froze(b)
    st.stills[still] = Still(name, held)
    one.stills.append(still)


def sprout(st, still, name):
    src = st.stills[still]
    head = dict(src.held)
    for b in head.values():
        hold.take(b)
    cell.spread(st, name, head, still)


def owner(st, still):
    return st.stills[still].owner


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
    above = cell.line(st, owner(st, still))
    moved = above.stills
    above.stills = []
    one.stills = moved + one.stills
    for each in moved:
        st.stills[each].owner = name
    one.origin = above.origin
    above.origin = still
