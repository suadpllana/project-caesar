from . import read
from . import say
from .edge import Edge
from .hold import Hold
from .pair import Pair
from .sched import Sched
from .tab import Tab
from .ver import Ver
from .wake import Wake

STEPS = 200000


def run(text):
    prog = read.parse(text)
    labels = {}
    for at, (op, args) in enumerate(prog.body):
        if op == "lab":
            labels[args[0]] = at

    tab = Tab(prog.log)
    edge = Edge(tab)
    pair = Pair(tab, prog.feed)
    hold = Hold()
    wake = Wake(tab)
    sched = Sched()
    ver = Ver(tab)
    out = say.Say()

    sched.open(0)
    steps = 0
    body = prog.body
    size = len(body)

    while True:
        who = sched.pick()
        if who is None:
            if edge.live():
                return finish(out, edge, 0)
            edge.cross()
            out.live()
            sched.release()
            continue

        if who.due is not None:
            deliver(out, pair, wake, hold, edge, who)

        while True:
            steps += 1
            if steps > STEPS:
                return out.over()
            if who.pc >= size:
                out.end(who.bid, who.acc)
                sched.close(who)
                if who.bid == 0:
                    return finish(out, edge, who.acc)
                break
            op, args = body[who.pc]
            who.pc += 1

            if op in read.KIND:
                kind = read.KIND[op]
                name = args[0]
                idx, slot = edge.slot(kind)
                if slot is not None:
                    if slot[1] != name:
                        return out.drift(kind, idx, slot[1], name)
                    edge.used(slot[0])
                rec = pair.bind(kind, name, idx, slot is not None)
                out.go(who.bid, kind, idx, name)
                hold.add(who.bid, rec)
                if op in read.AWAITS and park(sched, wake, out, pair, hold, edge, who,
                                              ("ok", rec)):
                    break
            elif op == "take":
                rec = hold.first(who.bid)
                if rec is not None and park(sched, wake, out, pair, hold, edge, who,
                                            ("ok", rec)):
                    break
            elif op == "wait":
                if park(sched, wake, out, pair, hold, edge, who, ("sig", args[0])):
                    break
            elif op == "fork":
                made = sched.open(labels[args[0]])
                out.fork(who.bid, made)
            elif op == "mark":
                got = ver.pick(args[0], int(args[1]), edge.live())
                who.acc = got
                out.ver(who.bid, args[0], got)
            elif op == "add":
                who.acc = who.acc + int(args[0])
            elif op == "set":
                who.acc = int(args[0])
            elif op == "jz":
                if who.acc == 0:
                    who.pc = labels[args[0]]
            elif op == "jnz":
                if who.acc != 0:
                    who.pc = labels[args[0]]
            elif op == "jmp":
                who.pc = labels[args[0]]
            elif op == "end":
                out.end(who.bid, who.acc)
                sched.close(who)
                if who.bid == 0:
                    return finish(out, edge, who.acc)
                break


def park(sched, wake, out, pair, hold, edge, who, due):
    who.due = due
    if edge.live():
        deliver(out, pair, wake, hold, edge, who)
        return False
    sched.park(who, wake.mark(who.bid, due))
    return True


def deliver(out, pair, wake, hold, edge, who):
    kind, payload = who.due
    who.due = None
    if kind == "ok":
        value = pair.settle(payload)
        hold.drop(who.bid, payload)
        who.acc = value
        out.ok(who.bid, payload.kind, payload.idx, value)
    else:
        value = wake.take(who.bid, payload, pair)
        who.acc = value
        out.sig(who.bid, payload, value)


def finish(out, edge, value):
    over = edge.leftover()
    if over is not None:
        return out.left(over[0], over[1])
    return out.fin(value)
