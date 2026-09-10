class Acct:
    def __init__(self):
        self.t = 0


def new():
    return Acct()


def born(a, b, t):
    a.t = t


def hold(a, v, x, b, t):
    a.t = t


def free(a, v, x, b, t):
    a.t = t
