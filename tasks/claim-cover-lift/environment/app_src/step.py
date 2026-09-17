from hb import book, door, tell


def ex(st, w):
    op = w[0]
    if op == "take":
        door.take(st, w[1], w[2], w[3])
    elif op == "drop":
        door.drop(st, w[1], w[2])
    elif op == "end":
        door.end(st, w[1])
    elif op == "show":
        tell.at(st, w[1], book.who(st, w[1]))
    elif op == "fill":
        job, box, mode = w[1], w[2], w[4]
        for i in range(1, int(w[3]) + 1):
            door.take(st, job, "%s:s%d" % (box, i), mode)
