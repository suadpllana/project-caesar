class Board:
    __slots__ = ("val", "gone", "link", "cur")

    def __init__(self):
        self.val = {}
        self.gone = set()
        self.link = {}
        self.cur = 0


def find(bd, sec, name):
    seen = set()
    at = sec
    while True:
        if at in seen:
            return None, None
        seen.add(at)
        key = (at, name)
        if key in bd.val:
            return at, bd.val[key]
        nxt = bd.link.get(at)
        if nxt is None:
            return None, None
        at = nxt


def read(bd, sec, name):
    return find(bd, sec, name)[1]
