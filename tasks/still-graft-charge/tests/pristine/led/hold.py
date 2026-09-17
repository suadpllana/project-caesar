class Blk:
    __slots__ = ("num", "size", "rc", "sc")

    def __init__(self, num, size):
        self.num = num
        self.size = size
        self.rc = 0
        self.sc = 0


def take(b):
    b.rc += 1


def give(b):
    b.rc -= 1


def froze(b):
    b.rc += 1
    b.sc += 1


def thaw(b):
    b.rc -= 1
    b.sc -= 1


def sole(st, b):
    return b.rc == 1


def kept(b):
    return b.sc > 0
