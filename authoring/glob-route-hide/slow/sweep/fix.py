"""Exactly correct, light on memory, and too slow: one sweep of the module graph per name.

Names are processed one group at a time - a group being names tied together by renames - in
the order renames need them, and for each group a worklist settles item-to-region maps over
every module. Nothing but the answers and the values some later rename reads is kept, so it
never runs out of memory; but on the large programs every name reaches every module, so each
sweep visits the whole graph, once per referenced name.
"""
from collections import deque

from fe import glob, own, vis


class Tab:
    pass


def groups(names, needs):
    """Strongly connected groups of the rename graph, dependencies first."""
    index, low, stack, on, out, n = {}, {}, [], set(), [], [0]
    for root in names:
        if root in index:
            continue
        work = [(root, iter(sorted(needs.get(root, ()))))]
        index[root] = low[root] = n[0]
        n[0] += 1
        stack.append(root)
        on.add(root)
        while work:
            v, it = work[-1]
            w = next(it, None)
            if w is None:
                work.pop()
                if work:
                    low[work[-1][0]] = min(low[work[-1][0]], low[v])
                if low[v] == index[v]:
                    comp = []
                    while True:
                        x = stack.pop()
                        on.discard(x)
                        comp.append(x)
                        if x == v:
                            break
                    out.append(comp)
                continue
            if w not in index:
                index[w] = low[w] = n[0]
                n[0] += 1
                stack.append(w)
                on.add(w)
                work.append((w, iter(sorted(needs.get(w, ())))))
            elif w in on:
                low[v] = min(low[v], index[w])
    return out


def settle(prog):
    tab = Tab()
    mods = prog.order
    mine = {p: own.names(prog, p) for p in mods}
    items = {p: [ln for ln in own.lines(prog, p) if ln.k == "item"] for p in mods}
    uses = {p: [ln for ln in own.lines(prog, p) if ln.k == "use"] for p in mods}
    globs = {p: [ln for ln in glob.lines(prog, p) if ln.src in prog.mods] for p in mods}
    needs, readers_of = {}, {}
    for p in mods:
        for ln in uses[p]:
            needs.setdefault(ln.bn, set()).add(ln.nm)
    wanted = {ln.nm for _p, ln in prog.refs}
    todo, seen = list(wanted), set(wanted)
    while todo:
        n = todo.pop()
        for m in needs.get(n, ()):
            if m not in seen:
                seen.add(m)
                todo.append(m)
    kept = {}
    answers = {}
    for group in groups(sorted(seen), needs):
        gset = set(group)
        val = {(p, n): {} for p in mods for n in group}
        back = {}
        for p in mods:
            for n in group:
                node = (p, n)
                if n in mine[p]:
                    for ln in items[p]:
                        if ln.nm == n:
                            d = vis.lvl(ln, p)
                            if d < val[node].get(ln.ix, 99):
                                val[node][ln.ix] = d
                    for ln in uses[p]:
                        if ln.bn == n and ln.src in prog.mods and ln.nm in gset:
                            back.setdefault((ln.src, ln.nm), []).append((node, ln))
                else:
                    for ln in globs[p]:
                        back.setdefault((ln.src, n), []).append((node, ln))
        # values from earlier groups that renames in this group read
        for p in mods:
            for n in group:
                if n in mine[p]:
                    for ln in uses[p]:
                        if ln.bn == n and ln.src in prog.mods and ln.nm not in gset:
                            src_val = kept.get((ln.src, ln.nm), {})
                            c, lv = vis.cpd(ln.src, p), vis.lvl(ln, p)
                            for ix, d in src_val.items():
                                if d <= c:
                                    nd = d if d > lv else lv
                                    if nd < val[(p, n)].get(ix, 99):
                                        val[(p, n)][ix] = nd
        work = deque(k for k, v in val.items() if v)
        queued = set(work)
        while work:
            node = work.popleft()
            queued.discard(node)
            src_val = val[node]
            for up, ln in back.get(node, ()):
                c, lv = vis.cpd(node[0], up[0]), vis.lvl(ln, up[0])
                cur = val[up]
                grew = False
                for ix, d in src_val.items():
                    if d <= c:
                        nd = d if d > lv else lv
                        if nd < cur.get(ix, 99):
                            cur[ix] = nd
                            grew = True
                if grew and up not in queued:
                    queued.add(up)
                    work.append(up)
        for p, ln in prog.refs:
            if ln.nm in gset:
                answers[(p, ln.nm)] = dict(val[(p, ln.nm)])
        for p in mods:
            for ln in uses[p]:
                if ln.nm in gset and ln.src in prog.mods:
                    kept[(ln.src, ln.nm)] = val[(ln.src, ln.nm)]
    tab.answers = answers
    tab.mine = mine
    return tab
