import operator

from sim import load

TESTS = {"eq": operator.eq, "ne": operator.ne, "lt": operator.lt, "ge": operator.ge}
ALU = {
    "add": operator.add,
    "sub": operator.sub,
    "mul": operator.mul,
    "slt": lambda x, y: int(x < y),
    "mod": operator.mod,
}
CACHED = {"spin.ca": True, "spin.cg": False, "ld.ca": True, "ld.cg": False}


def parked(launch, b):
    return launch.code[b.pc].op[:5] == "spin."


def idle(launch, mem, b):
    ins = launch.code[b.pc]
    v, moves = mem.probe(b.sm, load.ea(b, ins.at), CACHED[ins.op])
    return not moves and not TESTS[ins.cmp](v, load.val(launch, b, ins.b))


def _spin(launch, mem, b, ins, t):
    want = load.val(launch, b, ins.b)
    v, moves = mem.load(b.sm, load.ea(b, ins.at), CACHED[ins.op])
    b.reg[ins.rd] = v
    if TESTS[ins.cmp](v, want):
        b.pc += 1
        return "pass"
    return "moved" if moves else "idle"


def _mov(launch, mem, b, ins, t):
    b.reg[ins.rd] = load.val(launch, b, ins.a)


def _alu(launch, mem, b, ins, t):
    b.reg[ins.rd] = ALU[ins.op](load.val(launch, b, ins.a), load.val(launch, b, ins.b))


def _ld(launch, mem, b, ins, t):
    b.reg[ins.rd] = mem.load(b.sm, load.ea(b, ins.at), CACHED[ins.op])[0]


def _st(launch, mem, b, ins, t):
    mem.store(b.sm, load.ea(b, ins.at), load.val(launch, b, ins.a))


def _atom(launch, mem, b, ins, t):
    a, v = load.ea(b, ins.at), load.val(launch, b, ins.a)
    b.reg[ins.rd] = mem.atomic(a, v)


def _fence(launch, mem, b, ins, t):
    mem.fence(b.sm)


def _work(launch, mem, b, ins, t):
    b.free_at = t + max(1, load.val(launch, b, ins.a))


def _out(launch, mem, b, ins, t):
    b.outs.append(load.val(launch, b, ins.a))


def _jump(launch, mem, b, ins, t):
    op = ins.op
    if op == "bra" or (load.val(launch, b, ins.a) == 0) == (op == "brz"):
        b.pc = ins.to
        return "other"


def _exit(launch, mem, b, ins, t):
    b.end = t
    return "other"


DO = {"spin.ca": _spin, "spin.cg": _spin, "mov": _mov, "ld.ca": _ld, "ld.cg": _ld,
      "st": _st, "atom.add": _atom, "fence": _fence, "work": _work, "out": _out,
      "bra": _jump, "brz": _jump, "brnz": _jump, "exit": _exit}
DO.update((op, _alu) for op in ALU)


def execute(launch, mem, b, t):
    ins = launch.code[b.pc]
    kind = DO[ins.op](launch, mem, b, ins, t)
    if kind is None:
        b.pc += 1
        kind = "other"
    return kind
