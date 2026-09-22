"""One instruction of one block.

Every operand is read before the instruction writes anything. A spin makes exactly one
attempt per issue - the load it names, into its destination - and moves on only when the
comparison holds. The caller needs to know what kind of issue it was:

  QUIET   a failing attempt that changed no cache: repeating it changes nothing
  MOVED   a failing attempt that filled or dropped a line
  PASS    an attempt that got through
  OTHER   any other instruction
"""
from sim import load

QUIET, MOVED, PASS, OTHER = range(4)

TEST = {
    "eq": lambda x, y: x == y,
    "ne": lambda x, y: x != y,
    "lt": lambda x, y: x < y,
    "ge": lambda x, y: x >= y,
}

SPIN = ("spin.ca", "spin.cg")


def spinning(launch, b):
    return launch.code[b.pc].op in SPIN


def frozen(launch, mem, b):
    """Would this spinner's next attempt fail and leave its cache as it is?"""
    ins = launch.code[b.pc]
    got, changed = mem.peek(b.sm, load.ea(b, ins.at), ins.op == "spin.ca")
    return not changed and not TEST[ins.cmp](got, load.val(launch, b, ins.b))


def step(launch, mem, b, t):
    ins = launch.code[b.pc]
    op = ins.op
    r = b.reg
    if op in SPIN:
        a = load.ea(b, ins.at)
        want = load.val(launch, b, ins.b)
        got, changed = mem.ld(b.sm, a, op == "spin.ca")
        r[ins.rd] = got
        if TEST[ins.cmp](got, want):
            b.pc += 1
            return PASS
        return MOVED if changed else QUIET
    if op == "mov":
        r[ins.rd] = load.val(launch, b, ins.a)
    elif op in ("add", "sub", "mul", "slt", "mod"):
        x, y = load.val(launch, b, ins.a), load.val(launch, b, ins.b)
        if op == "add":
            r[ins.rd] = x + y
        elif op == "sub":
            r[ins.rd] = x - y
        elif op == "mul":
            r[ins.rd] = x * y
        elif op == "slt":
            r[ins.rd] = 1 if x < y else 0
        else:
            r[ins.rd] = x % y
    elif op == "ld.ca" or op == "ld.cg":
        r[ins.rd] = mem.ld(b.sm, load.ea(b, ins.at), op == "ld.ca")[0]
    elif op == "st":
        mem.st(b.sm, load.ea(b, ins.at), load.val(launch, b, ins.a))
    elif op == "atom.add":
        a, v = load.ea(b, ins.at), load.val(launch, b, ins.a)
        r[ins.rd] = mem.add(b.sm, a, v)
    elif op == "fence":
        mem.fence(b.sm)
    elif op == "work":
        b.busy = t + max(1, load.val(launch, b, ins.a))
    elif op == "bra":
        b.pc = ins.to
        return OTHER
    elif op == "brz" or op == "brnz":
        if (load.val(launch, b, ins.a) == 0) == (op == "brz"):
            b.pc = ins.to
            return OTHER
    elif op == "out":
        b.outs.append(load.val(launch, b, ins.a))
    elif op == "exit":
        b.end = t
        return OTHER
    b.pc += 1
    return OTHER
