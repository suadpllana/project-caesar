from bind import say


class Names:
    def __init__(self):
        self.firm = {}
        self.soft = {}
        self.need = {}
        self.spare = {}
        self.want = set()


def enter(names, job, p):
    for nm, strong in p.gives:
        if strong:
            if nm in names.firm:
                say.dup(job, nm, p.unit)
            else:
                names.firm[nm] = p
        elif nm not in names.soft:
            names.soft[nm] = p
        touch(names, nm)
    hint(names, p)


def hint(names, p):
    for nm, strong in p.uses:
        if strong:
            names.need[nm] = names.need.get(nm, 0) + 1
            touch(names, nm)


def spares(names, u):
    for nm, size in u.spares:
        if nm not in names.spare:
            names.spare[nm] = (size, u.name)
        touch(names, nm)


def touch(names, nm):
    if nm in names.firm or nm in names.soft:
        names.want.discard(nm)
    elif names.need.get(nm, 0) > 0 or nm in names.spare:
        names.want.add(nm)
    else:
        names.want.discard(nm)


def bind(names, nm):
    p = names.firm.get(nm)
    if p is None:
        p = names.soft.get(nm)
    return p
