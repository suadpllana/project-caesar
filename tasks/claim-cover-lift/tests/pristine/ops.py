from hb import gate, hold, say


def ex(st, w):
    op = w[0]
    if op == "take":
        gate.take(st, w[1], w[2], w[3])
    elif op == "drop":
        gate.drop(st, w[1], w[2])
    elif op == "end":
        gate.end(st, w[1])
    elif op == "show":
        say.at(st, w[1], hold.who(st, w[1]))
    elif op == "fill":
        job, box, mode = w[1], w[2], w[4]
        for i in range(1, int(w[3]) + 1):
            gate.take(st, job, "%s:s%d" % (box, i), mode)
