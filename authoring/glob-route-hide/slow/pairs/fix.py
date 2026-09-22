"""Exactly correct, and too slow: the textbook fixed point over (module, name) pairs.

Every pair a reference needs is found by walking the static dependency graph back from the
references - an own line for a name leads to its source pair, a glob to the same name in the
source - and a worklist settles item-to-region maps over that graph. It is the plan the rules
suggest when read one at a time, and on the trees every module holds every name, so the pairs
are the product of the module count and the name count.
"""
from collections import deque

from fe import glob, own, vis


class Tab:
    pass


def settle(prog):
    tab = Tab()
    mine = {p: own.names(prog, p) for p in prog.order}
    uses = {p: [ln for ln in own.lines(prog, p) if ln.k == "use"] for p in prog.order}
    items = {p: [ln for ln in own.lines(prog, p) if ln.k == "item"] for p in prog.order}
    globs = {p: glob.lines(prog, p) for p in prog.order}

    def deps(node):
        path, name = node
        if name in mine[path]:
            return [(ln, (ln.src, ln.nm)) for ln in uses[path]
                    if ln.bn == name and ln.src in prog.mods]
        return [(ln, (ln.src, name)) for ln in globs[path] if ln.src in prog.mods]

    val, dep, back = {}, {}, {}
    stack = [(p, ln.nm) for p, ln in prog.refs]
    while stack:
        node = stack.pop()
        if node in dep:
            continue
        dep[node] = deps(node)
        path, name = node
        val[node] = {}
        if name in mine[path]:
            for ln in items[path]:
                if ln.nm == name:
                    val[node][ln.ix] = min(val[node].get(ln.ix, 99), vis.lvl(ln, path))
        for ln, src in dep[node]:
            back.setdefault(src, []).append(node)
            if src not in dep:
                stack.append(src)
    work = deque(dep)
    queued = set(dep)
    while work:
        node = work.popleft()
        queued.discard(node)
        path, _name = node
        cur = val[node]
        grew = False
        for ln, src in dep[node]:
            c = vis.cpd(src[0], path)
            lv = vis.lvl(ln, path)
            for ix, d in val[src].items():
                if d <= c:
                    nd = d if d > lv else lv
                    if nd < cur.get(ix, 99):
                        cur[ix] = nd
                        grew = True
        if grew:
            for up in back.get(node, ()):
                if up not in queued:
                    queued.add(up)
                    work.append(up)
    tab.val = val
    tab.mine = mine
    return tab
