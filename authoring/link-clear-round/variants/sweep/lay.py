"""Variant: the groups are buckets, emptied in the direction the change asks for."""
from keep import halt, hit, reach, undo


class Work:
    __slots__ = ("st", "links", "find")

    def __init__(self, st, links):
        self.st = st
        self.links = links
        self.find = hit.Find(st, links)


def open(st, links):
    return Work(st, links)


def run(work, op, out):
    if op[0] == "put":
        work.st.add(op[1], op[2])
        work.find.add(op[1], work.st.get(op[1], op[2][0]))
        return
    kind, tab, key = op[0], op[1], op[2]
    if not work.st.has(tab, key):
        out.none(tab, key)
        return
    new = op[3] if kind == "mov" else None
    md, grp, order, bars = reach.walk(work, kind, tab, key, new)
    if order:
        li, ck = order[0]
        out.bar(work.links[li].name, bars[(li, ck)], ck)
        return
    stuck = halt.clash(work, md)
    if stuck is not None:
        out.clash(stuck[0], stuck[1])
        return
    log = undo.Log()
    where = {}
    for step in _steps(work, md, grp, kind):
        _lay(work, step, out, log, where)
    bad = halt.wait(work, kind, log)
    if bad is not None:
        li, kt, kk = bad
        out.wait(work.links[li].name, kt, kk)
        undo.back(work, log)


def _steps(work, md, grp, kind):
    buckets = {}
    for (tab, key), (gone, cols) in md.items():
        deep = grp[(tab, key)]
        at = work.st.tabs[tab].at
        here = buckets.setdefault(deep, [])
        if gone is not None:
            here.append((at, key, 0, tab, 0, "drop", None, gone))
        else:
            for ci, (act, val, li) in cols.items():
                here.append((at, key, ci, tab, ci, act, val, li))
    steps = []
    for deep in sorted(buckets, reverse=(kind == "out")):
        steps.extend(sorted(buckets[deep]))
    return steps


def _lay(work, step, out, log, where):
    was, tab, ci, act, val, li = step[1], step[3], step[4], step[5], step[6], step[7]
    name = work.links[li].name if li >= 0 else "-"
    seat = where.get((tab, was), was)
    log.touch(work, tab, seat)
    if act == "drop":
        work.find.gone(tab, work.st.get(tab, seat))
        work.st.take(tab, seat)
        out.drop(tab, was, name)
        return
    col = work.st.tabs[tab].cols[ci]
    old = work.st.get(tab, seat)[ci]
    if act == "clear":
        work.st.set(tab, seat, ci, None)
        work.find.wrote(tab, seat, ci, old, None)
        out.clear(tab, was, col, name)
        return
    if ci == 0:
        log.touch(work, tab, val)
        work.find.gone(tab, work.st.get(tab, seat))
        work.st.rekey(tab, seat, val)
        work.find.add(tab, work.st.get(tab, val))
        where[(tab, was)] = val
    else:
        work.st.set(tab, seat, ci, val)
        work.find.wrote(tab, seat, ci, old, val)
    out.move(tab, was, col, val, name)
