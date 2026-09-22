from led import close
from led import say
from led import work


def one(store, box, op, out):
    kind = op[0]
    if kind == "cfg":
        store.open(op[1])
        return
    if kind == "tx":
        box[op[1]] = work.Txn(op[1], store)
        return
    t = box[op[1]]
    if kind == "rd":
        t.taken.seen(op[2])
        out.append(say.read(t.num, op[2], t.held.at(op[2], t.taken)))
    elif kind == "put":
        t.held.put(op[2], op[3])
        t.sets(op[2])
    elif kind == "add":
        t.held.add(op[2], op[3], t.taken)
        t.sets(op[2])
    elif kind == "cpy":
        t.held.copy(op[2], op[3], t.taken)
        t.sets(op[2])
    elif kind == "raw":
        t.held.raw(op[2], op[3], t.taken)
        t.sets(op[2])
    elif kind == "bmp":
        for k in range(op[2], op[3]):
            t.held.add(k, op[4], t.taken)
            t.sets(k)
    elif kind == "chk":
        if t.held.at(op[2], t.taken) != op[3]:
            t.bad = True
    elif kind == "lim":
        if t.held.at(op[2], t.taken) < op[3]:
            t.bad = True
    elif kind == "mk":
        t.mark()
    elif kind == "un":
        t.cut()
    elif kind == "drp":
        del box[op[1]]
    elif kind == "fin":
        out.append(close.shut(store, t))
        del box[op[1]]
