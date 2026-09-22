from cf import sect


def settle(bk, bd, one):
    woke = False
    for i in range(bk.upto):
        ent = bk.ents[i]
        if ent.guard != "once" or i in bk.awake or not bk.stands(i):
            continue
        if sect.read(bd, bd.cur, ent.g) == ent.w:
            bk.awake.add(i)
            one(bk, bd, i)
            woke = True
    return 2 if woke else 1
