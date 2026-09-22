class Tune(object):
    __slots__ = ("horizon", "slack", "cap")

    def __init__(self, horizon, slack, cap):
        self.horizon = horizon
        self.slack = slack
        self.cap = cap


class Prog(object):
    __slots__ = ("tune", "span", "ops")

    def __init__(self, tune, span, ops):
        self.tune = tune
        self.span = span
        self.ops = ops


def parse(text):
    tune = Tune(0, 0, 1)
    top = 0
    ops = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        bits = line.split()
        tag = bits[0]
        if tag == "h":
            tune = Tune(int(bits[1]), int(bits[2]), int(bits[3]))
        elif tag == "w":
            k = int(bits[1])
            ops.append(("w", k, int(bits[2]), 0))
            if k > top:
                top = k
        elif tag == "x":
            k = int(bits[1])
            ops.append(("x", k, 0, 0))
            if k > top:
                top = k
        elif tag == "c":
            ops.append(("c", 0, 0, 0))
        elif tag == "r":
            lo = int(bits[1])
            hi = int(bits[2])
            ops.append(("r", lo, hi, int(bits[3])))
            if hi > top:
                top = hi
        else:
            raise ValueError(line)
    return Prog(tune, top + 1, ops)
