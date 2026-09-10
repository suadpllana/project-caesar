class Rec:
    __slots__ = ("id", "at", "size", "live")

    def __init__(self, name):
        self.id = name
        self.at = -1
        self.size = 0
        self.live = False


class Pool:
    def __init__(self, span, part):
        self.span = span
        self.part = part
        self.ids = {}


def get(h, name):
    r = h.ids.get(name)
    if r is None:
        r = h.ids[name] = Rec(name)
    return r
