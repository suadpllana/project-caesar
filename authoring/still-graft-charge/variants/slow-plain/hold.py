class Blk:
    __slots__ = ("num", "size", "by")

    def __init__(self, num, size):
        self.num = num
        self.size = size
        self.by = {}


def add(b, name):
    b.by[name] = b.by.get(name, 0) + 1


def off(b, name):
    n = b.by.get(name, 0) - 1
    if n <= 0:
        b.by.pop(name, None)
    else:
        b.by[name] = n


def who(b):
    return set(b.by)
