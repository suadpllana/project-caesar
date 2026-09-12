from bind import say


class Names:
    """What each name has been given by, and which names are still wanted.

    A name keeps every strong give it has collected, in arrival order, because the first of
    them can leave: one slot answers every program in which nothing is ever displaced and
    cannot say what the name falls back to. Wantedness is a count rather than a flag for the
    same reason - it moves down as well as up, so it cannot be latched.
    """

    def __init__(self):
        self.firm = {}
        self.soft = {}
        self.need = {}
        self.spare = {}
        self.want = set()


def enter(names, job, p):
    """A kept part's gives and uses arrive."""
    for nm, strong in p.gives:
        if strong:
            row = names.firm.setdefault(nm, [])
            if row:
                say.dup(job, nm, p.unit)
                del row[:]
            row.append(p)
        else:
            names.soft.setdefault(nm, []).append(p)
        touch(names, nm)
    for nm, strong in p.uses:
        if strong:
            names.need[nm] = names.need.get(nm, 0) + 1
            touch(names, nm)


def leave(names, p):
    """A displaced part's gives and uses go back out. No report, and no second give."""
    for nm, strong in p.gives:
        row = names.firm.get(nm) if strong else names.soft.get(nm)
        if row:
            for i, q in enumerate(row):
                if q is p:
                    del row[i]
                    break
        touch(names, nm)
    for nm, strong in p.uses:
        if strong:
            names.need[nm] = names.need.get(nm, 0) - 1
            touch(names, nm)


def spares(names, u, order):
    for nm, size in u.spares:
        names.spare.setdefault(nm, []).append((size, order, u.name))
        touch(names, nm)


def touch(names, nm):
    if names.firm.get(nm):
        names.want.discard(nm)
    elif names.need.get(nm, 0) > 0 or nm in names.spare:
        names.want.add(nm)
    else:
        names.want.discard(nm)


def bind(names, nm):
    """The part a name stands on: the first strong give, else the first weak one."""
    row = names.firm.get(nm)
    if row:
        return row[0]
    row = names.soft.get(nm)
    if row:
        return row[0]
    return None
