SPECIAL = ("%bid", "%sm", "%nb")
TESTS = ("eq", "ne", "lt", "ge")


class Launch:
    def __init__(self):
        self.sms = self.slots = self.lines = self.grid = None
        self.mem = {}
        self.show = []
        self.code = []


class Ins:
    def __init__(self, op, rd=None, a=None, b=None, at=None, cmp=None, to=None):
        self.op = op
        self.rd = rd
        self.a = a
        self.b = b
        self.at = at
        self.cmp = cmp
        self.to = to


class Blk:
    def __init__(self, n):
        self.n = n
        self.pc = 0
        self.reg = [0] * 8
        self.outs = []
        self.sm = None
        self.at = None
        self.end = None


def reg(tok):
    if len(tok) == 2 and tok[0] == "r" and tok[1] in "01234567":
        return int(tok[1])
    raise ValueError("bad register %r" % tok)


def opnd(tok):
    if tok in SPECIAL:
        return (tok, None)
    if tok.startswith("r"):
        return ("r", reg(tok))
    return ("k", int(tok))


def addr(tok):
    if not (tok.startswith("[") and tok.endswith("]")):
        raise ValueError("bad address %r" % tok)
    body = tok[1:-1]
    if body.startswith("r"):
        base, _, off = body.partition("+")
        return (reg(base), int(off) if off else 0)
    return (None, int(body))


def val(launch, blk, x):
    kind, v = x
    if kind == "r":
        return blk.reg[v]
    if kind == "k":
        return v
    if kind == "%bid":
        return blk.n
    if kind == "%sm":
        return blk.sm
    return launch.grid


def ea(blk, at):
    r, off = at
    return (blk.reg[r] if r is not None else 0) + off


def decode(f, labels):
    op, x = f[0], f[1:]
    if op == "mov":
        return Ins(op, rd=reg(x[0]), a=opnd(x[1]))
    if op in ("add", "sub", "mul", "slt"):
        return Ins(op, rd=reg(x[0]), a=opnd(x[1]), b=opnd(x[2]))
    if op == "mod":
        k = int(x[2])
        if k <= 0:
            raise ValueError("mod by %d" % k)
        return Ins(op, rd=reg(x[0]), a=opnd(x[1]), b=("k", k))
    if op in ("ld.ca", "ld.cg"):
        return Ins(op, rd=reg(x[0]), at=addr(x[1]))
    if op == "st":
        return Ins(op, at=addr(x[0]), a=opnd(x[1]))
    if op == "atom.add":
        return Ins(op, rd=reg(x[0]), at=addr(x[1]), a=opnd(x[2]))
    if op == "fence" or op == "exit":
        return Ins(op)
    if op in ("spin.ca", "spin.cg"):
        rd, at, b = reg(x[0]), addr(x[1]), opnd(x[3])
        if x[2] not in TESTS:
            raise ValueError("bad test %r" % x[2])
        if at[0] == rd or b == ("r", rd):
            raise ValueError("spin reads its own destination")
        return Ins(op, rd=rd, at=at, cmp=x[2], b=b)
    if op in ("sum.ca", "sum.cg"):
        k = int(x[2])
        if k <= 0:
            raise ValueError("sum of %d lines" % k)
        return Ins(op, rd=reg(x[0]), at=addr(x[1]), b=("k", k))
    if op == "work" or op == "out":
        return Ins(op, a=opnd(x[0]))
    if op == "bra":
        return Ins(op, to=labels[x[0]])
    if op in ("brz", "brnz"):
        return Ins(op, a=opnd(x[0]), to=labels[x[1]])
    raise ValueError("bad op %r" % op)


def parse(text):
    lc = Launch()
    body = None
    for raw in text.splitlines():
        s = raw.strip()
        if not s:
            continue
        if body is not None:
            body.append(s)
            continue
        f = s.split()
        if f[0] == "dev":
            lc.sms, lc.slots, lc.lines = (int(v) for v in f[1:4])
        elif f[0] == "grid":
            lc.grid = int(f[1])
        elif f[0] == "mem":
            lc.mem[int(f[1])] = int(f[2])
        elif f[0] == "show":
            lc.show.extend(int(v) for v in f[1:])
        elif f[0] == "prog":
            body = []
        else:
            raise ValueError("bad line %r" % s)
    if body is None or lc.grid is None or lc.sms is None:
        raise ValueError("incomplete launch")
    labels, rows = {}, []
    for s in body:
        if s.endswith(":"):
            labels[s[:-1]] = len(rows)
        else:
            rows.append(s.split())
    lc.code = [decode(f, labels) for f in rows]
    return lc
