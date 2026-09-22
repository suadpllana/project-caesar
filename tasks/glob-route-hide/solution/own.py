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
