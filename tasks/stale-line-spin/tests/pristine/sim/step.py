from sim import load

TEST = {
    "eq": lambda x, y: x == y,
    "ne": lambda x, y: x != y,
    "lt": lambda x, y: x < y,
    "ge": lambda x, y: x >= y,
}


def arith(op, x, y):
    if op == "add":
        return x + y
    if op == "sub":
        return x - y
    if op == "mul":
        return x * y
    if op == "slt":
        return 1 if x < y else 0
    return x % y


def step(launch, mem, b, t):
    ins = launch.code[b.pc]
    op = ins.op
    v = lambda x: load.val(launch, b, x)
    b.pc += 1
    if op == "mov":
        b.reg[ins.rd] = v(ins.a)
    elif op in ("add", "sub", "mul", "slt", "mod"):
        b.reg[ins.rd] = arith(op, v(ins.a), v(ins.b))
    elif op in ("ld.ca", "ld.cg"):
        b.reg[ins.rd] = mem.ld(b, load.ea(b, ins.at), op == "ld.ca")
    elif op == "st":
        a = load.ea(b, ins.at)
        mem.st(b, a, v(ins.a))
        return a
    elif op == "atom.add":
        a = load.ea(b, ins.at)
        b.reg[ins.rd] = mem.add(b, a, v(ins.a))
        return a
    elif op == "fence":
        mem.fence(b)
    elif op in ("sum.ca", "sum.cg"):
        b.reg[ins.rd] = mem.lines(load.ea(b, ins.at), ins.b[1])
    elif op in ("spin.ca", "spin.cg"):
        a = load.ea(b, ins.at)
        want = v(ins.b)
        b.reg[ins.rd] = mem.ld(b, a, op == "spin.ca")
        if not TEST[ins.cmp](b.reg[ins.rd], want):
            b.pc -= 1
            b.wait = a
    elif op == "work":
        b.busy = t + max(1, v(ins.a))
    elif op == "bra":
        b.pc = ins.to
    elif op in ("brz", "brnz"):
        if (v(ins.a) == 0) == (op == "brz"):
            b.pc = ins.to
    elif op == "out":
        b.outs.append(v(ins.a))
    elif op == "exit":
        b.end = t
    return None
