from train import ckpt


def play(cx, ops):
    for op in ops:
        o = op.get("op")
        if o == "micro":
            for _ in range(int(op.get("n", 1))):
                cx.loop.micro()
        elif o == "save":
            cx.mt.saves += 1
            cx.ck.put(ckpt.pack_state(cx))
            cx.tr.append("S:%d" % cx.loop.step)
        elif o == "kill":
            cx.down()
            cx.tr.append("K")
        elif o == "load":
            cx.mt.loads += 1
            cx.up()
            ckpt.unpack_state(cx, cx.ck.get())
            cx.tr.append("L:%d" % cx.loop.step)
        elif o == "amend":
            cx.amend(op.get("sched") or {}, op.get("top") or {})
            cx.tr.append("A")
        else:
            raise ValueError("unknown op %r" % (o,))
    return cx.report()
