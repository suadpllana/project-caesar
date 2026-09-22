from cf import gate, sect

MARKS = {"clr": ("e",), "cut": ("m",)}


def plan(st, ent, sec, pos, trail):
    if not gate.ok(st, ent, sec, pos, trail):
        return None, None
    kind = ent.kind
    if kind == "sec":
        return ("sec",), ent.a
    if kind == "lnk":
        return ("l", sec), ("l", ent.a)
    key = ("s", sec, ent.a)
    if kind == "set":
        return key, ("v", ent.b)
    if kind in MARKS:
        return key, MARKS[kind]
    found = sect.read(st, sec, ent.a, pos, trail)
    if found is None:
        return None, None
    return key, ("v", found + ent.b)
