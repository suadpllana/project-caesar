#!/bin/bash
# exact and light on memory: one sweep of the module graph for each referenced name
set -euo pipefail

cat > /app/fe/vis.py <<'PYEOF'
"""Visibility as a region depth.

A candidate that a module M holds is always seen from M itself, so the region it can be seen
from is either every module or the subtree of one of M's ancestors (M included). That makes the
region a single number relative to M: 0 for every module, d >= 1 for the subtree of M's
ancestor at depth d. Along a chain of lines the region only ever shrinks, and across routes the
widest one counts, so for any one candidate the regions it arrives with are totally ordered.

A module's holdings are kept as cumulative sets: cs[t] is every binding the module holds that
is seen from a region of depth t or wider. cs[dep(M)] is everything the module holds.
"""


def lvl(ln, path):
    """Region depth of what line `ln` of module `path` passes on: every module, or its own subtree."""
    return 0 if ln.pb else dep(path)


def take(cs, src, dst, lv, top):
    """What module `dst` receives through a line of level `lv` from `src`'s cumulative sets.

    A binding held at `src` with region depth d is seen from `dst` exactly when d is no deeper
    than the common prefix of the two paths, and it arrives with the narrower of its own region
    and the line's: depth max(d, lv). So for every t no shallower than `lv`, the bindings
    reaching `dst` at depth t or wider are those `src` holds at depth min(t, common prefix),
    and nothing reaches `dst` at a depth shallower than `lv`.
    """
    c = cpd(src, dst)
    out = [0] * (top + 1)
    for t in range(lv, top + 1):
        out[t] = cs[t if t < c else c]
    return out


def dep(path):
    return path.count(".") + 1


def cpd(a, b):
    n = 0
    for x, y in zip(a.split("."), b.split(".")):
        if x != y:
            break
        n += 1
    return n
PYEOF

cat > /app/fe/own.py <<'PYEOF'
"""What a module binds itself, and what its own lines give it.

A module binds a name itself when it has a present item line or explicit import line for that
name. That is decided by the lines alone - never by what an import turns out to find - which is
what keeps the whole resolution monotone: a glob candidate is hidden or not before anything has
been resolved, for every reader alike.
"""
from fe import flag, vis


def lines(prog, path):
    """The present item and explicit import lines of module `path`."""
    md = prog.mods.get(path)
    if md is None:
        return []
    return [ln for ln in md.lns if ln.k in ("item", "use") and flag.live(ln, prog.on)]


def names(prog, path):
    """Every name module `path` binds itself, whatever its lines find."""
    return {ln.nm if ln.k == "item" else ln.bn for ln in lines(prog, path)}


def alloc(prog, tab):
    """Give every (item, name) pair a candidate can ever be held under its own bit.

    An item starts under its own name; a present `use P::N as K` can carry anything held under
    N on to K, so the pairs are closed under those renames. The closure over-approximates -
    it ignores whether the source ever holds the item - which only costs unused bits.
    """
    for ix, (_path, ln) in enumerate(prog.items):
        add(tab, ix, ln.nm)
    renames = set()
    for path in prog.order:
        for ln in lines(prog, path):
            if ln.k == "use" and ln.bn != ln.nm:
                renames.add((ln.nm, ln.bn))
    grew = True
    while grew:
        grew = False
        for nm, bn in renames:
            for ix in list(tab.ids.get(nm, ())):
                if (ix, bn) not in tab.bit:
                    add(tab, ix, bn)
                    grew = True


def add(tab, ix, name):
    b = len(tab.bit)
    tab.bit[(ix, name)] = b
    tab.ids.setdefault(name, []).append(ix)
    tab.nmask[name] = tab.nmask.get(name, 0) | (1 << b)


def base(prog, tab, path):
    """Cumulative sets holding only the module's own present items, at their lines' regions."""
    top = tab.top[path]
    out = [0] * (top + 1)
    for ln in lines(prog, path):
        if ln.k != "item":
            continue
        b = 1 << tab.bit[(ln.ix, ln.nm)]
        for t in range(vis.lvl(ln, path), top + 1):
            out[t] |= b
    return out


def gives(prog, tab, path, out):
    """OR into `out` what the module's present explicit imports give it now.

    `use P::N as K` takes what P holds under N that this module can see, narrowed to the
    import line's region, and holds it under K. It is taken whatever this module binds itself:
    the line is one of the module's own bindings of K.
    """
    top = tab.top[path]
    for ln in lines(prog, path):
        if ln.k != "use":
            continue
        cs = tab.cs.get(ln.src)
        if cs is None:
            continue
        got = vis.take(cs, ln.src, path, vis.lvl(ln, path), top)
        mk = tab.nmask.get(ln.nm, 0)
        for t in range(top + 1):
            x = got[t] & mk
            if x and ln.bn != ln.nm:
                x = carry(tab, x, ln.nm, ln.bn)
            out[t] |= x


def carry(tab, x, nm, bn):
    """Move the bits of `x`, all held under `nm`, to the same items held under `bn`."""
    y = 0
    for ix in tab.ids[nm]:
        if x >> tab.bit[(ix, nm)] & 1:
            y |= 1 << tab.bit[(ix, bn)]
    return y
PYEOF

cat > /app/fe/glob.py <<'PYEOF'
"""What a module's globs give it.

A present `use P::*` gives the importing module, under every name the module does not bind
itself, whatever P holds under that name that the importing module can see, narrowed to the
glob line's region. Hiding is a mask over whole names, applied whoever will read the result.
"""
from fe import flag, vis


def lines(prog, path):
    """The present glob lines of module `path`."""
    md = prog.mods.get(path)
    if md is None:
        return []
    return [ln for ln in md.lns if ln.k == "glob" and flag.live(ln, prog.on)]


def gives(prog, tab, path, out):
    """OR into `out` what the module's present globs give it now, minus its own names."""
    top = tab.top[path]
    keep = ~tab.mine[path]
    for ln in lines(prog, path):
        cs = tab.cs.get(ln.src)
        if cs is None:
            continue
        got = vis.take(cs, ln.src, path, vis.lvl(ln, path), top)
        for t in range(top + 1):
            if got[t]:
                out[t] |= got[t] & keep
PYEOF

cat > /app/fe/fix.py <<'PYEOF'
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
PYEOF

cat > /app/fe/say.py <<'PYEOF'
def line(prog, tab, i):
    path, ln = prog.refs[i]
    name = ln.nm
    got = sorted(tab.answers.get((path, name), {}))
    shown = ["%s.%s" % (prog.items[ix][0], prog.items[ix][1].nm) for ix in got]
    if len(shown) == 1:
        return "%s %s %s" % (path, name, shown[0])
    if not shown:
        return "%s %s %s" % (path, name, "broken" if name in tab.mine[path] else "unresolved")
    return "%s %s ambiguous %s" % (path, name, " ".join(shown))
PYEOF

