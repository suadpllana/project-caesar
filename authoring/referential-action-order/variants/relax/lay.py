"""Variant: the same contract, over a store that is written through the lookup."""
from keep import halt, hit, reach, undo


class Work:
    __slots__ = ("st", "links", "find", "fan")

    def __init__(self, st, links):
        self.st = st
        self.links = links
        self.find = hit.Find(st, links)
        self.fan = {}
        for li, ln in enumerate(links):
            self.fan.setdefault(ln.par, []).append((li, ln))


def open(st, links):
    return Work(st, links)


def run(work, op, out):
    if op[0] == "put":
        work.find.saved = None
        work.find.put(op[1], op[2][0], list(op[2]))
        return
    kind, tab, key = op[0], op[1], op[2]
    if not work.st.has(tab, key):
        out.none(tab, key)
        return
    new = op[3] if kind == "mov" else None
    md, grp, bars = reach.walk(work, kind, tab, key, new)
    if bars:
        li, kt, kk = min(bars, key=lambda b: (b[0], b[2]))
        out.bar(work.links[li].name, kt, kk)
        return
    stuck = halt.clash(work, md)
    if stuck is not None:
        out.clash(stuck[0], stuck[1])
        return
    work.find.saved = {}
    where = {}
    for step in _steps(work, md, grp, kind):
        _lay(work, step, out, where)
    bad = halt.wait(work, kind)
    if bad is not None:
        li, kt, kk = bad
        out.wait(work.links[li].name, kt, kk)
        undo.back(work)


def _steps(work, md, grp, kind):
    steps = []
    for (tab, key), here in md.items():
        at = work.st.tabs[tab].at
        deep = grp[(tab, key)]
        rank = -deep if kind == "out" else deep
        if here.gone is not None:
            steps.append((rank, at, key, 0, tab, 0, "drop", None, here.gone))
        else:
            for ci in sorted(here.cols):
                act, val, li = here.cols[ci]
                steps.append((rank, at, key, ci, tab, ci, act, val, li))
    steps.sort(key=lambda s: s[:4])
    return steps


def _lay(work, step, out, where):
    was, tab, ci, act, val, li = step[2], step[4], step[5], step[6], step[7], step[8]
    name = work.links[li].name if li >= 0 else "-"
    seat = where.get((tab, was), was)
    row = list(work.st.get(tab, seat))
    if act == "drop":
        work.find.put(tab, seat, None)
        out.drop(tab, was, name)
        return
    col = work.st.tabs[tab].cols[ci]
    if act == "clear":
        row[ci] = None
        work.find.put(tab, seat, row)
        out.clear(tab, was, col, name)
        return
    row[ci] = val
    if ci == 0:
        work.find.put(tab, seat, None)
        work.find.put(tab, val, row)
        where[(tab, was)] = val
    else:
        work.find.put(tab, seat, row)
    out.move(tab, was, col, val, name)
