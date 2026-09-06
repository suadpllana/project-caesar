from . import vocab


def lead(b):
    if b[:1] == b" ":
        return b[1:]
    return b


class Pcs:
    def __init__(self):
        self.k = 0

    def step(self, i):
        if vocab.sp(i):
            return b""
        b = vocab.bs(i)
        if self.k == 0:
            b = lead(b)
        self.k += 1
        return b
