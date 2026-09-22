from led import close
from led import say
from led import take
from led import work


def one(store, box, op, out):
    kind = op[0]
    if kind == "cfg":
        store.open(op[1])
        return
    if kind == "tx":
        t = work.Txn(op[1])
        t.see(store, tuple(sorted(store.val)))
        box[op[1]] = t
        return
    t = box[op[1]]
    t.see(store, take.names(op))
    if kind == "rd":
        k = op[2]
        v = t.held.at(k, t.taken)
        out.append(say.read(t.num, k, v))
        t.note(("f", k, v))
        t.held.stick(k, v)
    elif kind == "put":
        k = op[2]
        t.sets(k, ("p", k, op[3]))
        t.held.put(k, op[3])
    elif kind == "add":
        k = op[2]
        t.sets(k, ("a", k, op[3]))
        t.held.add(k, op[3])
    elif kind == "cpy":
        k = op[2]
        t.sets(k, ("c", k, op[3]))
        t.held.copy(k, op[3])
    elif kind == "raw":
        k = op[2]
        t.sets(k, ("r", k, op[3]))
        t.held.raw(k, op[3])
    elif kind == "bmp":
        for k in range(op[2], op[3]):
            t.sets(k, ("a", k, op[4]))
            t.held.add(k, op[4])
    elif kind == "chk":
        t.note(("k", op[2], op[3]))
    elif kind == "lim":
        t.note(("l", op[2], op[3]))
    elif kind == "mk":
        t.mark()
    elif kind == "un":
        t.cut()
    elif kind == "drp":
        del box[op[1]]
    elif kind == "fin":
        out.append(close.shut(store, t))
        del box[op[1]]
