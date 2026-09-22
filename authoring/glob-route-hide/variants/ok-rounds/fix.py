from fe import glob, own, vis


class Tab:
    __slots__ = ("pos", "holders", "mask", "held", "depth", "bound")


def settle(prog):
    tab = Tab()
    tab.pos, tab.holders, tab.mask = {}, {}, {}

    def new(ix, name):
        if (ix, name) not in tab.pos:
            b = len(tab.pos)
            tab.pos[(ix, name)] = b
            tab.holders.setdefault(name, []).append(ix)
            tab.mask[name] = tab.mask.get(name, 0) | (1 << b)

    for ix, (_p, ln) in enumerate(prog.items):
        new(ix, ln.nm)
    carried = {(ln.nm, ln.bn) for p in prog.order for ln in own.present(prog, p)
               if ln.k == "use" and ln.nm != ln.bn}
    size = -1
    while size != len(tab.pos):
        size = len(tab.pos)
        for nm, bn in carried:
            for ix in list(tab.holders.get(nm, ())):
                new(ix, bn)

    tab.depth = {p: vis.dep(p) for p in prog.order}
    tab.bound = {p: own.bound(prog, p) for p in prog.order}
    keep = {}
    for p in prog.order:
        m = 0
        for n in tab.bound[p]:
            m |= tab.mask.get(n, 0)
        keep[p] = ~m

    lines = {p: (own.present(prog, p), glob.present(prog, p)) for p in prog.order}
    held = {p: [0] * (tab.depth[p] + 1) for p in prog.order}
    while True:
        nxt = {}
        for p in prog.order:
            acc = [0] * (tab.depth[p] + 1)
            mine, globs = lines[p]
            for ln in mine:
                if ln.k == "item":
                    acc[vis.level(ln, p)] |= 1 << tab.pos[(ln.ix, ln.nm)]
                elif ln.src in held:
                    lv = vis.level(ln, p)
                    for d, bits in vis.spread(held[ln.src], ln.src, p, lv).items():
                        bits &= tab.mask.get(ln.nm, 0)
                        if bits and ln.bn != ln.nm:
                            moved = 0
                            for ix in tab.holders[ln.nm]:
                                if bits >> tab.pos[(ix, ln.nm)] & 1:
                                    moved |= 1 << tab.pos[(ix, ln.bn)]
                            bits = moved
                        acc[d] |= bits
            for ln in globs:
                if ln.src in held:
                    lv = vis.level(ln, p)
                    for d, bits in vis.spread(held[ln.src], ln.src, p, lv).items():
                        acc[d] |= bits & keep[p]
            nxt[p] = vis.settle_depths(acc)
        if nxt == held:
            break
        held = nxt
    tab.held = held
    return tab
