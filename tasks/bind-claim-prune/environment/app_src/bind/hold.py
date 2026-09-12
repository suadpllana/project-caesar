class Keep:
    def __init__(self):
        self.loaded = set()
        self.parts = {}
        self.who = {}


def load(keep, u):
    ins = []
    drop = []
    for p in u.parts:
        if p.key is not None and p.key in keep.who:
            drop.append(p)
            continue
        if p.key is not None:
            keep.who[p.key] = (p.unit, p.idx)
        keep.parts[(p.unit, p.idx)] = p
        ins.append(p)
    return ins, drop
