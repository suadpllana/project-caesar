from cf import sect


def ok(st, ent, sec, pos, saw):
    if ent.guard != "if":
        return True
    return sect.read(st, sec, ent.g, pos, saw) == ent.w
