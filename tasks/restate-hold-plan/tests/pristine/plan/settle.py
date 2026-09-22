from plan.keep import there
from plan.look import looks


def settle(pp, got):
    rows = []
    for name, i in got:
        if name not in pp.reads or not there(pp, name, i):
            continue
        if (name, i) in pp.pins:
            rows.append(("hold", name, i, "pinned"))
        elif all(there(pp, src, p) for src, p in looks(pp, name, i)):
            rows.append(("run", name, i, "full"))
        else:
            rows.append(("hold", name, i, "lost"))
    return rows
