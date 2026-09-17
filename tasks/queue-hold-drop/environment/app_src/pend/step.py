from . import fold, hold, line, store, view


def run(st, op):
    k = op[0]
    if k == "new":
        line.take(st, store.Chg("new", op[1], op[2]))
    elif k == "set":
        line.take(st, store.Chg("set", op[1], op[2], int(op[3])))
    elif k == "add":
        line.take(st, store.Chg("add", op[1], op[2], int(op[3])))
    elif k == "mov":
        line.take(st, store.Chg("mov", op[1], op[2]))
    elif k == "cut":
        line.take(st, store.Chg("cut", op[1]))
    elif k == "snd":
        hold.send(st)
    elif k == "ok":
        fold.answer(st, True)
    elif k == "no":
        fold.answer(st, False)
    elif k == "oth":
        j = op[1]
        if j == "new":
            view.land(st, store.Chg("new", op[2], op[3]))
        elif j == "set":
            view.land(st, store.Chg("set", op[2], op[3], int(op[4])))
        elif j == "add":
            view.land(st, store.Chg("add", op[2], op[3], int(op[4])))
        elif j == "mov":
            view.land(st, store.Chg("mov", op[2], op[3]))
        elif j == "cut":
            view.land(st, store.Chg("cut", op[2]))
    elif k == "ask":
        view.ask(st, op[1])
    elif k == "all":
        view.all(st)
