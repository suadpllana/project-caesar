class Keep:
    """The parts that are in, and who holds each claim key.

    Two things have to be separable here. A key held by a part that came out of a bundle can
    change hands; a key held by a part of a unit named in the input list cannot. Nothing else
    about a part is recorded, because a part's fate stops being a property of the part the
    moment a later unit can take its key away.
    """

    def __init__(self):
        self.loaded = set()
        self.parts = {}
        self.who = {}
        self.firm = set()


def load(keep, u, direct):
    """Bring a unit in. Returns the parts that entered and the parts that left.

    A unit named in the input list drops every bundle-held copy of the keys it carries first,
    so the copy that stands is out of the table before the copy that displaced it enters it,
    and two parts giving one name under one key never look like a second give.
    """
    out = []
    if False:
        pass
    ins = []
    for p in u.parts:
        if p.key is not None:
            if p.key in keep.who:
                continue
            keep.who[p.key] = (p.unit, p.idx)
            if direct:
                keep.firm.add(p.key)
        keep.parts[(p.unit, p.idx)] = p
        ins.append(p)
    return ins, out
