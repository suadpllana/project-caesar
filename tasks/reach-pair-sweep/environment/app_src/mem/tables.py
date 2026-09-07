class Ref:
    __slots__ = ("tgt", "wiped")

    def __init__(self, tgt):
        self.tgt = tgt
        self.wiped = False


class Pair:
    __slots__ = ("key", "kser", "val")

    def __init__(self, key, kser, val):
        self.key = key
        self.kser = kser
        self.val = val
