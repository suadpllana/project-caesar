from . import read
from . import say
from .edge import Edge
from .pair import Pair
from .pend import Pend
from .sigq import Sigq
from .tab import Tab
from .ver import Ver

STEPS = 200000


def run(text):
    prog = read.parse(text)
    tab = Tab(prog.log)
    edge = Edge(tab)
    pair = Pair(tab, prog.feed)
    pend = Pend()
    sigq = Sigq(tab)
    ver = Ver(tab)
    out = say.Say()

    labels = {}
    for at, (op, args) in enumerate(prog.body):
        if op == "lab":
            labels[args[0]] = at

    acc = 0
    pc = 0
    steps = 0
    n = len(prog.body)
    while pc < n:
        steps += 1
        if steps > STEPS:
            return out.over()
        op, args = prog.body[pc]
        pc += 1
        if op in read.KIND:
            kind = read.KIND[op]
            name = args[0]
            idx, slot, opened = edge.slot(kind)
            if opened:
                out.live()
            if slot is not None:
                if slot[1] != name:
                    return out.drift(kind, idx, slot[1], name)
                edge.used(slot[0])
            rec = pair.bind(kind, name, idx, slot is not None)
            out.go(kind, idx, name)
            if op in read.TAKES:
                if rec.value is None:
                    return out.hold(kind, idx)
                acc = rec.value
                out.ok(kind, idx, rec.value)
            else:
                pend.add(rec)
        elif op == "join" or op == "race":
            if pend.empty():
                return out.holdnone()
            rec = pend.first() if op == "join" else pend.fastest()
            if rec.value is None:
                return out.hold(rec.kind, rec.idx)
            pend.drop(rec)
            acc = rec.value
            out.ok(rec.kind, rec.idx, rec.value)
        elif op == "wait":
            got = sigq.take(args[0])
            if got is None:
                return out.holdsig(args[0])
            acc = got
            out.sig(args[0], got)
        elif op == "mark":
            got = ver.pick(args[0], int(args[1]), edge.live())
            acc = got
            out.ver(args[0], got)
        elif op == "add":
            acc = acc + int(args[0])
        elif op == "set":
            acc = int(args[0])
        elif op == "jz":
            if acc == 0:
                pc = labels[args[0]]
        elif op == "jnz":
            if acc != 0:
                pc = labels[args[0]]
        elif op == "jmp":
            pc = labels[args[0]]
        elif op == "fin":
            break
    over = edge.leftover()
    if over is not None:
        return out.left(over[0], over[1])
    return out.fin(acc)
