from keep import cover


class Acct:
    def __init__(self):
        self.made = {}
        self.roll = []
        self.at = {}
        self.pegs = {}
        self.by = {}
        self.stop = {}
        self.out = set()
        self.t = 0


def new():
    return Acct()


def born(a, b, t):
    a.t = t
    a.made[b] = t
    a.roll.append(b)


def hold(a, v, x, b, t):
    a.t = t
    r = a.at.get(b)
    if r is None:
        a.at[b] = [v, t, None]
    else:
        r[2] = None


def free(a, v, x, b, t):
    a.t = t
    r = a.at.get(b)
    if r is not None:
        r[2] = t
    if b not in a.stop and not cover.kept(a, b):
        a.stop[b] = t
