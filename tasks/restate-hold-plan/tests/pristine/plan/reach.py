from plan.keep import there
from plan.span import last, takes


def readers(pp):
    back = {}
    for name in pp.names:
        if name not in pp.reads:
            continue
        for i in range(last(pp, name) + 1):
            for _kind, src, parts in takes(pp, name, i):
                for p in parts:
                    back.setdefault((src, p), []).append((name, i))
    return back


def reach(pp):
    back = readers(pp)
    got = {pp.fix}
    todo = [pp.fix]
    while todo:
        at = todo.pop()
        for up in back.get(at, ()):
            if up not in got and there(pp, *up):
                got.add(up)
                todo.append(up)
    return got
