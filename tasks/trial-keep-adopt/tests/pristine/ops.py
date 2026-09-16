from fld import defs, feed, hold, need, say


def ex(f, w):
    op = w[0]
    if op == "def":
        defs.add(f, w[1], w[2], tuple(w[3:]))
    elif op == "set":
        feed.put(f, w[1], int(w[2]))
    elif op == "ask":
        say.val(f, w[1], need.get(f, w[1]))
    elif op == "pin":
        need.pin(f, w[1])
    elif op == "free":
        need.free(f, w[1])
    elif op == "try":
        hold.on(f, w[1], int(w[2]))
    elif op == "end":
        hold.off(f)
    elif op == "bulk":
        tag, n, step = w[1], int(w[2]), int(w[3])
        for i in range(n):
            a = "%sa%d" % (tag, i)
            b = "%sb%d" % (tag, i)
            defs.add(f, a, "raw", ())
            defs.add(f, b, "cap", (a, "500"))
            defs.add(f, "%sc%d" % (tag, i), "sum", (b, b))
            feed.put(f, a, i % step + 1)
    else:
        raise ValueError("no such op: %s" % op)
