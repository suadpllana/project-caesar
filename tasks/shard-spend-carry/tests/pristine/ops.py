from opt import keep, lay, say, tick


def ex(r, t):
    op = t[0]
    r.clock += 1
    if op == "grd":
        tick.grad(r, t[1], int(t[2]))
    elif op == "step":
        tick.step(r)
    elif op == "par":
        lay.add(r, t[1], int(t[2]))
    elif op == "frz":
        lay.down(r, t[1])
    elif op == "thw":
        lay.up(r, t[1])
    elif op == "ws":
        lay.wide(r, int(t[1]))
    elif op == "bud":
        r.bud = int(t[1])
    elif op == "save":
        keep.save(r, t[1])
    elif op == "load":
        keep.load(r, t[1])
    elif op == "own":
        say.own(r, int(t[1]))
    elif op == "val":
        say.show(r, t[1], 0)
    elif op == "mom":
        say.show(r, t[1], 1)
    else:
        raise ValueError(op)
