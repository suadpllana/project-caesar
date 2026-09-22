from dbg import frames, marks, steps


def play(img, link, cmds, out):
    locs = set()
    eng = steps.Engine(img, link, locs)
    count = 0
    for raw in cmds:
        w = raw.split()
        if not w:
            continue
        if w[0] == "break":
            count += 1
            where = marks.resolve(img, int(w[1]))
            locs.update(where)
            out(" ".join(["b%d" % count] + [str(a) for a in where]))
            continue
        kind = {
            "run": eng.run,
            "cont": eng.cont,
            "step": eng.step,
            "next": eng.next,
            "finish": eng.finish,
        }[w[0]]()
        if kind is None:
            out("exit")
            continue
        pc = link.pc()
        shown = frames.show(img, pc, link.stack(), eng.hid)
        out(" ".join([kind, str(pc)] + ["%s:%d" % f for f in shown]))
