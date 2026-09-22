from cf import book, gate, sect, step, tell, wake


def one(bk, bd, i):
    ent = bk.ents[i]
    if not bk.stands(i):
        return
    if ent.guard == "once" and i not in bk.awake:
        return
    if not gate.ok(bd, ent):
        return
    book.note(bk, bd, i)
    step.act(bd, ent)


def play(prog, out):
    bk = book.Book(prog)
    bd = sect.Board()
    for stp in prog.steps:
        head = stp[0]
        if head == "ent":
            bk.upto = stp[1] + 1
            one(bk, bd, stp[1])
        elif head == "off":
            bk.dead.add(stp[1])
            for i in reversed(bk.own[stp[1]]):
                if i < bk.upto:
                    book.undo(bk, bd, i)
        elif head == "back":
            bk.dead.discard(stp[1])
            for i in bk.own[stp[1]]:
                if i < bk.upto:
                    one(bk, bd, i)
        elif head == "get":
            passes = wake.settle(bk, bd, one)
            tell.one(out, stp[1], stp[2], sect.read(bd, stp[1], stp[2]), passes)
        else:
            passes = wake.settle(bk, bd, one)
            tell.board(out, bd, passes)
