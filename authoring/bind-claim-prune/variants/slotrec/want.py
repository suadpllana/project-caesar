from bind import say


class Slot:
    __slots__ = ("firm", "soft", "need", "spare")

    def __init__(self):
        self.firm = []
        self.soft = []
        self.need = 0
        self.spare = []


class Names:
    def __init__(self):
        self.slot = {}
        self.want = set()
        self.fresh = []

    def at(self, nm):
        s = self.slot.get(nm)
        if s is None:
            s = self.slot[nm] = Slot()
        return s


def touch(names, nm):
    s = names.slot.get(nm)
    if s is None:
        return
    if not s.firm and (s.need > 0 or s.spare):
        if nm not in names.want:
            names.want.add(nm)
            names.fresh.append(nm)
    else:
        names.want.discard(nm)


def enter(names, job, p):
    for nm, strong in p.gives:
        s = names.at(nm)
        if strong:
            if s.firm:
                say.dup(job, nm, p.unit)
            s.firm.append(p)
        else:
            s.soft.append(p)
        touch(names, nm)
    for nm, strong in p.uses:
        if strong:
            names.at(nm).need += 1
            touch(names, nm)


def leave(names, p):
    for nm, strong in p.gives:
        s = names.at(nm)
        row = s.firm if strong else s.soft
        for i in range(len(row)):
            if row[i] is p:
                del row[i]
                break
        touch(names, nm)
    for nm, strong in p.uses:
        if strong:
            names.at(nm).need -= 1
            touch(names, nm)


def spares(names, u, order):
    for nm, size in u.spares:
        names.at(nm).spare.append((size, order, u.name))
        touch(names, nm)


def bind(names, nm):
    s = names.slot.get(nm)
    if s is None:
        return None
    if s.firm:
        return s.firm[0]
    if s.soft:
        return s.soft[0]
    return None
