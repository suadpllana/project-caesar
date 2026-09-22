import re

TOKEN = re.compile(r"[a-z][a-z0-9]*|[(),*]")


class Entry:
    def __init__(self, idx, name, opened, bound, ret, params):
        self.idx = idx
        self.name = name
        self.opened = opened
        self.bound = bound
        self.ret = ret
        self.params = params


class Node:
    def __init__(self, name, args, site):
        self.name = name
        self.args = args
        self.site = site


class Result:
    def __init__(self, how, kind, binds, pins):
        self.how = how
        self.kind = kind
        self.binds = binds
        self.pins = pins


class Prog:
    def __init__(self):
        self.kinds = []
        self.ups = {}
        self.entries = []
        self.vals = {}
        self.asks = []


def expr(text):
    toks = TOKEN.findall(text)
    at = [0]
    seen = [0]

    def one():
        name = toks[at[0]]
        at[0] += 1
        if at[0] < len(toks) and toks[at[0]] == "(":
            site = seen[0]
            seen[0] += 1
            at[0] += 1
            args = [one()]
            while toks[at[0]] == ",":
                at[0] += 1
                args.append(one())
            at[0] += 1
            return Node(name, args, site)
        return Node(name, None, None)

    return one()


def parse(text):
    prog = Prog()
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        head, _, rest = line.partition(" ")
        rest = rest.strip()
        if head == "kind":
            prog.kinds.append(rest)
            prog.ups[rest] = []
        elif head == "rise":
            a, b = rest.split()
            prog.ups[a].append(b)
        elif head == "entry":
            bits = rest.split()
            prog.entries.append(
                Entry(len(prog.entries), bits[0], False, None, bits[1], bits[2:]))
        elif head == "open":
            bits = rest.split()
            prog.entries.append(
                Entry(len(prog.entries), bits[0], True, bits[1], bits[2], bits[3:]))
        elif head == "val":
            a, b = rest.split()
            prog.vals[a] = b
        elif head == "ask":
            prog.asks.append(expr(rest))
        else:
            raise ValueError(line)
    return prog
