from led import cell, cost, free, gate, say, tree


def ex(st, w):
    op = w[0]
    if op == "line":
        cell.mkline(st, w[1])
    elif op == "cap":
        gate.cap(st, w[1], int(w[2]))
    elif op == "put":
        gate.put(st, w[1], int(w[2]), int(w[3]), int(w[4]))
    elif op == "cut":
        cell.erase(st, w[1], int(w[2]), int(w[3]))
    elif op == "still":
        tree.freeze(st, w[1], w[2])
    elif op == "graft":
        tree.sprout(st, w[1], w[2])
    elif op == "lift":
        tree.lift(st, w[1])
    elif op == "drop":
        free.drop(st, w[1])
    elif op == "ask":
        say.charge(st, w[1], cost.charge(st, w[1]))
    elif op == "at":
        say.at(st, w[1], int(w[2]), cell.at(st, w[1], int(w[2])))
