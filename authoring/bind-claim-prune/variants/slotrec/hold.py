class Keep:
    def __init__(self):
        self.loaded = set()
        self.parts = {}
        self.owner = {}
        self.fixed = set()


def load(keep, u, direct):
    gone = []
    if direct:
        for p in u.parts:
            if p.key and p.key in keep.owner and p.key not in keep.fixed:
                gone.append(keep.parts.pop(keep.owner.pop(p.key)))
    took = []
    for p in u.parts:
        if p.key:
            if p.key in keep.owner:
                continue
            keep.owner[p.key] = (p.unit, p.idx)
            if direct:
                keep.fixed.add(p.key)
        keep.parts[(p.unit, p.idx)] = p
        took.append(p)
    return took, gone
