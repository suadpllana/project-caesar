from bay import desc


def covers(st, deps, view, ent):
    for s in deps:
        if s in view and desc.runs(st, view[s], deps[s]):
            continue
        if s in ent:
            continue
        return False
    return True
