"""Exactly correct, and too slow: a full table per module.

Each module holds a dict from (item, name) to the widest region depth it is seen from, and a
worklist re-derives a module from its sources' tables whenever one of them grows. Correct, and
on the trees every table holds every binding of the program, which is quadratic in memory and
in the work of copying one table into the next.
"""
from collections import deque

from fe import glob, own, vis


class Tab:
    pass


def settle(prog):
    tab = Tab()
    mine = {p: own.names(prog, p) for p in prog.order}
    lines = {p: (own.lines(prog, p), glob.lines(prog, p)) for p in prog.order}
    held = {}
    readers = {}
    for p in prog.order:
        t = {}
        for ln in lines[p][0]:
            if ln.k == "item":
                k = (ln.ix, ln.nm)
                t[k] = min(t.get(k, 99), vis.lvl(ln, p))
            elif ln.src in prog.mods:
                readers.setdefault(ln.src, set()).add(p)
        for ln in lines[p][1]:
            if ln.src in prog.mods:
                readers.setdefault(ln.src, set()).add(p)
        held[p] = t
    work = deque(prog.order)
    queued = set(prog.order)
    while work:
        p = work.popleft()
        queued.discard(p)
        cur = held[p]
        grew = False

        def put(k, d):
            nonlocal grew
            if d < cur.get(k, 99):
                cur[k] = d
                grew = True

        own_lines, globs = lines[p]
        for ln in own_lines:
            if ln.k != "use" or ln.src not in prog.mods:
                continue
            c = vis.cpd(ln.src, p)
            lv = vis.lvl(ln, p)
            for (ix, nm), d in list(held[ln.src].items()):
                if nm == ln.nm and d <= c:
                    put((ix, ln.bn), d if d > lv else lv)
        for ln in globs:
            if ln.src not in prog.mods:
                continue
            c = vis.cpd(ln.src, p)
            lv = vis.lvl(ln, p)
            for (ix, nm), d in list(held[ln.src].items()):
                if nm not in mine[p] and d <= c:
                    put((ix, nm), d if d > lv else lv)
        if grew:
            for r in readers.get(p, ()):
                if r not in queued:
                    queued.add(r)
                    work.append(r)
    tab.held = held
    tab.mine = mine
    return tab
