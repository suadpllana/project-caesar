from cf import gate, sect


def plan(st, ent, sec, pos, saw):
    if saw is not None:
        saw[1].add(sec)
    if not gate.ok(st, ent, sec, pos, saw):
        return None, None
    kind = ent.kind
    if kind == "sec":
        return ("sec",), ent.a
    if kind == "lnk":
        return ("l", sec), ("l", ent.a)
    if saw is not None:
        saw[0].add(ent.a)
    key = ("s", sec, ent.a)
    if kind == "set":
        return key, ("v", ent.b)
    if kind == "clr":
        return key, ("e",)
    if kind == "cut":
        return key, ("m",)
    found = sect.read(st, sec, ent.a, pos, saw)
    if found is None:
        return None, None
    return key, ("v", found + ent.b)
