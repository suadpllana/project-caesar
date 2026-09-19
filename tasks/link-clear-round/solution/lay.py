"""Deciding a change in full, then laying it down.

The order the lines come out in is not the order the reach found them. Groups go deepest
first when the change takes a row out, because nothing may be taken out while something still
points at it, and shallowest first when it re-keys one, because no pointer may be moved onto
a key before the row holding it has taken that key. Inside a group the order is the store's
own: table, then the key the row had when the change began, then column.

A row can take a new key and have another column written in the same change, and the key line
sorts first, so everything after it has to find the row under the key it now has while still
naming the key it began with.
"""
from keep import halt, hit, reach, undo


class Work:
    __slots__ = ("st", "links", "find", "fan", "order")

    def __init__(self, st, links):
        self.st = st
        self.links = links
        self.find = hit.Find(st, links)
        self.fan = {}
        for li, ln in enumerate(links):
            self.fan.setdefault(ln.par, []).append((li, ln))
        self.order = _order(st.tabs, links)


def _order(tabs, links):
    """Tables with every parent before its children. Two links onto one pair count twice."""
    down = {name: [] for name in tabs}
    into = {name: 0 for name in tabs}
    for ln in links:
        down[ln.par].append(ln.kid)
        into[ln.kid] += 1
    ready = [n for n in tabs if into[n] == 0]
    out = []
    while ready:
        ready.sort(key=lambda n: tabs[n].at)
        name = ready.pop(0)
        out.append(name)
        for nxt in down[name]:
            into[nxt] -= 1
            if into[nxt] == 0:
                ready.append(nxt)
    return out


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
    md, grp, bars = reach.walk(work, kind, tab, key, new)
    if bars:
        li, kt, kk = min(bars, key=lambda b: (b[0], b[2]))
        out.bar(work.links[li].name, kt, kk)
        return
    stuck = halt.clash(work, md)
    if stuck is not None:
        out.clash(stuck[0], stuck[1])
        return
    log = undo.Log()
    lost = {}
    now = {}
    for step in _steps(work, md, grp, kind):
        _lay(work, step, out, log, lost, now)
    lost = {t: {k for k in ks if not work.st.has(t, k)} for t, ks in lost.items()}
    bad = halt.wait(work, kind, lost)
    if bad is not None:
        li, kt, kk = bad
        out.wait(work.links[li].name, kt, kk)
        undo.back(work, log)


def _steps(work, md, grp, kind):
    steps = []
    for tab, by in md.rows.items():
        at = work.st.tabs[tab].at
        for key, here in by.items():
            deep = grp[(tab, key)]
            if here.gone is not None:
                steps.append((deep, at, key, 0, tab, 0, "drop", None, here.gone))
            else:
                for ci, (knd, val, li) in here.cols.items():
                    steps.append((deep, at, key, ci, tab, ci, knd, val, li))
    steps.sort(key=lambda s: ((-s[0] if kind == "out" else s[0]), s[1], s[2], s[3]))
    return steps


def _lay(work, step, out, log, lost, now):
    was, tab, ci, knd, val, li = step[2], step[4], step[5], step[6], step[7], step[8]
    name = work.links[li].name if li >= 0 else "-"
    key = now.get((tab, was), was)
    if knd == "drop":
        row = work.st.get(tab, key)
        work.find.gone(tab, row)
        log.gone(tab, row)
        work.st.take(tab, key)
        lost.setdefault(tab, set()).add(key)
        out.drop(tab, was, name)
        return
    col = work.st.tabs[tab].cols[ci]
    if knd == "clear":
        old = work.st.get(tab, key)[ci]
        log.wrote(tab, key, ci, old)
        work.st.set(tab, key, ci, None)
        work.find.wrote(tab, key, ci, old, None)
        out.clear(tab, was, col, name)
        return
    if ci == 0:
        work.find.gone(tab, work.st.get(tab, key))
        log.rekeyed(tab, key, val)
        work.st.rekey(tab, key, val)
        work.find.add(tab, work.st.get(tab, val))
        lost.setdefault(tab, set()).add(key)
        now[(tab, was)] = val
    else:
        old = work.st.get(tab, key)[ci]
        log.wrote(tab, key, ci, old)
        work.st.set(tab, key, ci, val)
        work.find.wrote(tab, key, ci, old, val)
    out.move(tab, was, col, val, name)
