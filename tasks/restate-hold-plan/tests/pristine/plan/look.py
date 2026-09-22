from plan.span import takes


def looks(pp, name, i):
    out = []
    for _kind, src, parts in takes(pp, name, i):
        for p in parts:
            out.append((src, p))
    return out
