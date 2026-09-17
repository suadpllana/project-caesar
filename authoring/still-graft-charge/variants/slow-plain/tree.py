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
        hold.add(b, name)
    st.stills[still] = Still(name, held)
    one.stills.append(still)


def sprout(st, still, name):
    src = st.stills[still]
    head = dict(src.held)
    for b in head.values():
        hold.add(b, name)
    cell.spread(st, name, head, still)


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
    up = st.stills[still].owner
    above = cell.line(st, up)
    cut = above.stills.index(still) + 1
    moved = above.stills[:cut]
    above.stills = above.stills[cut:]
    one.stills = moved + one.stills
    for each in moved:
        rec = st.stills[each]
        rec.owner = name
        for b in rec.held.values():
            hold.off(b, up)
            hold.add(b, name)
    one.origin = above.origin
    above.origin = still
