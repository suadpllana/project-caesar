from view import hold, spec, tree


def run(text):
    prog = spec.parse(text)
    v = tree.View(prog)
    hold.start(v)
    out = []
    for n, ops in enumerate(prog.frames, 1):
        hold.before(v)
        for op in ops:
            v.apply(op)
        s, tag = hold.after(v)
        v.s = s
        del v.log[:]
        out.append("%d %d %s" % (n, s, tag))
    return out
