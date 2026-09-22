from sim import load


def tail(b):
    return "".join(" %d" % v for v in b.outs)


def lines(launch, blocks, hang, left, gm):
    out = []
    for b in blocks:
        if b.end is not None:
            out.append("blk %d sm %d at %d end %d%s" % (b.n, b.sm, b.at, b.end, tail(b)))
    if hang is not None:
        out.append("hang %d" % hang)
        for b in blocks:
            if b.at is not None and b.end is None:
                on = load.ea(b, launch.code[b.pc].at)
                out.append("spin %d sm %d at %d on %d%s" % (b.n, b.sm, b.at, on, tail(b)))
        out.append("left %d" % left)
    for a in launch.show:
        out.append("mem %d %d" % (a, gm.get(a, 0)))
    return out
