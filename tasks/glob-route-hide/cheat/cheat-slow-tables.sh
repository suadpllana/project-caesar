#!/bin/bash
# exact: a full table per module, one dict per module holding every binding it has
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
PYEOF

cat > /app/fe/say.py <<'PYEOF'
def line(prog, tab, i):
    path, ln = prog.refs[i]
    name = ln.nm
    got = sorted(ix for (ix, nm) in tab.held[path] if nm == name)
    shown = ["%s.%s" % (prog.items[ix][0], prog.items[ix][1].nm) for ix in got]
    if len(shown) == 1:
        return "%s %s %s" % (path, name, shown[0])
    if not shown:
        return "%s %s %s" % (path, name, "broken" if name in tab.mine[path] else "unresolved")
    return "%s %s ambiguous %s" % (path, name, " ".join(shown))
PYEOF

