"""Exactly correct: the wanted set is what the kept parts say it is, so it is read off them
again after every load rather than carried."""
from bind import say


class Names:
    def __init__(self):
        self.firm = {}
        self.soft = {}
        self.spare = {}
        self.want = set()


def enter(names, job, p):
    for nm, strong in p.gives:
        if strong:
            row = names.firm.setdefault(nm, [])
            if row:
                say.dup(job, nm, p.unit)
            row.append(p)
        else:
            names.soft.setdefault(nm, []).append(p)


def leave(names, p):
    for nm, strong in p.gives:
        row = names.firm.get(nm) if strong else names.soft.get(nm)
        if row:
            for i, q in enumerate(row):
                if q is p:
                    del row[i]
                    break


def spares(names, u, order):
    for nm, size in u.spares:
        names.spare.setdefault(nm, []).append((size, order, u.name))


def rebuild(names, keep):
    names.want.clear()
    for p in keep.parts.values():
        for nm, strong in p.uses:
            if strong and not names.firm.get(nm):
                names.want.add(nm)
    for nm in names.spare:
        if not names.firm.get(nm):
            names.want.add(nm)


def bind(names, nm):
    row = names.firm.get(nm)
    if row:
        return row[0]
    row = names.soft.get(nm)
    if row:
        return row[0]
    return None
