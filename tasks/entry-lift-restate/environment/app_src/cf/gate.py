from cf import sect


def ok(bd, ent):
    if ent.guard is None:
        return True
    if ent.kind in ("sec", "lnk"):
        return True
    return sect.read(bd, bd.cur, ent.g) == ent.w
