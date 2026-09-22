from res import kind


def cands(prog, name, count):
    return [ent for ent in prog.entries
            if ent.name == name and len(ent.params) == count]


def opens(ent):
    return [i for i, p in enumerate(ent.params) if p == "*"]


def slots(ent, settled):
    return [settled if p == "*" else p for p in ent.params]


def result(ent, settled):
    return settled if ent.ret == "*" else ent.ret


def in_bound(prog, ent, settled):
    return kind.steps(prog, ent.bound, settled) is not None
