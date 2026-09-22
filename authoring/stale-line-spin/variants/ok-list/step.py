from sim import load

OPS = {
    "add": lambda x, y: x + y,
    "sub": lambda x, y: x - y,
    "mul": lambda x, y: x * y,
    "slt": lambda x, y: int(x < y),
    "mod": lambda x, y: x % y,
}
CMP = {
    "eq": lambda x, y: x == y,
    "ne": lambda x, y: x != y,
    "lt": lambda x, y: x < y,
    "ge": lambda x, y: x >= y,
}


def at_spin(launch, b):
    return launch.code[b.pc].op.startswith("spin")


def idle_attempt(launch, mem, b):
    ins = launch.code[b.pc]
    v, moves = mem.load(b.sm, load.ea(b, ins.at), ins.op == "spin.ca", touch=False)
    return not moves and not CMP[ins.cmp](v, load.val(launch, b, ins.b))


def run_one(launch, mem, b, t):
    """Returns 'idle', 'moved', 'passed' or 'done'."""
    ins = launch.code[b.pc]
    op = ins.op
    val = lambda x: load.val(launch, b, x)
    nxt = b.pc + 1
    kind = "done"
    if op.startswith("spin"):
        want = val(ins.b)
        v, moves = mem.load(b.sm, load.ea(b, ins.at), op == "spin.ca")
        b.reg[ins.rd] = v
        if CMP[ins.cmp](v, want):
            kind = "passed"
        else:
            nxt = b.pc
            kind = "moved" if moves else "idle"
    elif op == "mov":
        b.reg[ins.rd] = val(ins.a)
    elif op in OPS:
        b.reg[ins.rd] = OPS[op](val(ins.a), val(ins.b))
    elif op.startswith("ld."):
        b.reg[ins.rd] = mem.load(b.sm, load.ea(b, ins.at), op == "ld.ca")[0]
    elif op == "st":
        mem.store(b.sm, load.ea(b, ins.at), val(ins.a))
    elif op == "atom.add":
        a = load.ea(b, ins.at)
        b.reg[ins.rd] = mem.atomic(a, val(ins.a))
    elif op == "fence":
        mem.fence(b.sm)
    elif op == "work":
        b.until = t + max(1, val(ins.a))
    elif op == "bra":
        nxt = ins.to
    elif op == "brz":
        if val(ins.a) == 0:
            nxt = ins.to
    elif op == "brnz":
        if val(ins.a) != 0:
            nxt = ins.to
    elif op == "out":
        b.outs.append(val(ins.a))
    elif op == "exit":
        b.end = t
        return kind
    b.pc = nxt
    return kind
