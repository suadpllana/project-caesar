from cf import gate, sect


def plan(st, ent, sec, pos, trail):
    if not gate.ok(st, ent, sec, pos, trail):
        return None, None
    kind = ent.kind
    if kind == "sec":
        return ("sec",), ent.a
    if kind == "lnk":
        return ("l", sec), ("l", ent.a)
    if kind == "add":
        found = sect.read(st, sec, ent.a, pos, trail)
        if found is None:
            return None, None
        return ("s", sec, ent.a), ("v", found + ent.b)
    key = ("s", sec, ent.a)
    if kind == "set":
        return key, ("v", ent.b)
    if kind == "clr":
        return key, ("e",)
    return key, ("m",)
