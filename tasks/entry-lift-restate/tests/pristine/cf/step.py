from cf import sect


def target(bd, ent):
    if ent.kind == "add":
        at, _found = sect.find(bd, bd.cur, ent.a)
        return (bd.cur if at is None else at, ent.a)
    return (bd.cur, ent.a)


def act(bd, ent):
    kind = ent.kind
    if kind == "sec":
        bd.cur = ent.a
        return
    if kind == "lnk":
        bd.link[bd.cur] = ent.a
        return
    key = target(bd, ent)
    if kind == "set":
        bd.val[key] = ent.b
        bd.gone.discard(key)
    elif kind == "clr":
        bd.val.pop(key, None)
        bd.gone.discard(key)
    elif kind == "cut":
        bd.val.pop(key, None)
        bd.gone.add(key)
    elif kind == "add":
        found = sect.read(bd, bd.cur, ent.a)
        bd.val[key] = (0 if found is None else found) + ent.b
        bd.gone.discard(key)
