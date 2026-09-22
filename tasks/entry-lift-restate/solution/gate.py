from cf import sect


def ok(st, ent, sec, pos, trail):
    if ent.guard != "if":
        return True
    return sect.read(st, sec, ent.g, pos, trail) == ent.w
