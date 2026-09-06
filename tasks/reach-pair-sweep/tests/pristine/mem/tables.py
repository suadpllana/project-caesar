class Ref:
    __slots__ = ("tgt", "wiped")

    def __init__(self, tgt):
        self.tgt = tgt
        self.wiped = False


def by_key(h):
    out = {}
    for k, v in h.pairs:
        out.setdefault(k, []).append(v)
    return out


def drop_gone(h, gone):
    if not gone:
        return
    h.pairs[:] = [(k, v) for k, v in h.pairs if k not in gone and v not in gone]
