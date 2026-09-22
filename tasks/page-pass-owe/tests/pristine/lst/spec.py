class Prog(object):
    def __init__(self, hold, ops):
        self.hold = hold
        self.ops = ops


def load(text):
    hold = 0
    ops = []
    for raw in text.splitlines():
        f = raw.split()
        if not f:
            continue
        if f[0] == "cfg":
            hold = int(f[1])
        else:
            ops.append(tuple([f[0]] + [int(x) for x in f[1:]]))
    return Prog(hold, ops)
