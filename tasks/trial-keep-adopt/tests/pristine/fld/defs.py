ARITY = {"raw": 0, "cap": 2, "pick": 3, "gate": 2}
LIT = {("cap", 1)}


def add(f, name, kind, args):
    if kind == "sum":
        if len(args) < 2:
            raise ValueError("sum takes two or more")
    elif kind not in ARITY:
        raise ValueError("no such form: %s" % kind)
    elif len(args) != ARITY[kind]:
        raise ValueError("%s takes %d" % (kind, ARITY[kind]))
    if name in f.kind:
        raise ValueError("already defined: %s" % name)
    for i, a in enumerate(args):
        if (kind, i) in LIT:
            continue
        if a not in f.kind:
            raise ValueError("%s reads %s before it is defined" % (name, a))
    f.kind[name] = kind
    f.args[name] = args
    if kind == "raw":
        f.pub[name] = 0


def src(f, name):
    return f.kind[name] == "raw"
