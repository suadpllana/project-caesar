from collections import deque

from fe import glob, own, vis


class Tab:
    def __init__(self):
        self.slot = {}
        self.under = {}
        self.names = {}
        self.held = {}
        self.mine = {}

    def bit(self, ix, name):
        b = self.slot.get((ix, name))
        if b is None:
            b = self.slot[(ix, name)] = len(self.slot)
            self.under.setdefault(name, []).append(ix)
            self.names[name] = self.names.get(name, 0) | (1 << b)
        return b

    def hidden(self, path):
        m = 0
        for n in self.mine[path]:
            m |= self.names.get(n, 0)
        return m


def components(order, deps):
    index, low, on, stack, out = {}, {}, set(), [], []
    counter = [0]
    for root in order:
        if root in index:
            continue
        work = [(root, iter(deps[root]))]
        index[root] = low[root] = counter[0]
        counter[0] += 1
        stack.append(root)
        on.add(root)
        while work:
            node, it = work[-1]
            nxt = next(it, None)
            if nxt is None:
                work.pop()
                if work:
                    parent = work[-1][0]
                    low[parent] = min(low[parent], low[node])
                if low[node] == index[node]:
                    comp = []
                    while True:
                        w = stack.pop()
                        on.discard(w)
                        comp.append(w)
                        if w == node:
                            break
                    out.append(comp)
                continue
            if nxt not in index:
                index[nxt] = low[nxt] = counter[0]
                counter[0] += 1
                stack.append(nxt)
                on.add(nxt)
                work.append((nxt, iter(deps[nxt])))
            elif nxt in on:
                low[node] = min(low[node], index[nxt])
    return out


def settle(prog):
    tab = Tab()
    for ix, (_p, ln) in enumerate(prog.items):
        tab.bit(ix, ln.nm)
    uses, globs, deps = {}, {}, {}
    for p in prog.order:
        tab.mine[p] = own.names(prog, p)
        uses[p] = [ln for ln in own.lines(prog, p) if ln.k == "use"]
        globs[p] = glob.lines(prog, p)
        tab.held[p] = {}
        for ln in own.lines(prog, p):
            if ln.k == "item":
                vis.absorb(tab.held[p], {vis.edge_level(ln, p): 1 << tab.bit(ln.ix, ln.nm)})
        deps[p] = sorted({ln.src for ln in uses[p] + globs[p] if ln.src in prog.mods})

    def derive(p):
        got_all = []
        for ln in uses[p]:
            got = vis.arriving(tab.held[ln.src], ln.src, p, vis.edge_level(ln, p)) \
                if ln.src in tab.held else {}
            for d, bits in got.items():
                bits &= tab.names.get(ln.nm, 0)
                if bits and ln.bn != ln.nm:
                    moved = 0
                    for ix in list(tab.under[ln.nm]):
                        if bits >> tab.slot[(ix, ln.nm)] & 1:
                            moved |= 1 << tab.bit(ix, ln.bn)
                    bits = moved
                if bits:
                    got_all.append({d: bits})
        hide = tab.hidden(p)
        for ln in globs[p]:
            if ln.src not in tab.held:
                continue
            got = vis.arriving(tab.held[ln.src], ln.src, p, vis.edge_level(ln, p))
            got = {d: b & ~hide for d, b in got.items() if b & ~hide}
            if got:
                got_all.append(got)
        changed = False
        for got in got_all:
            if vis.absorb(tab.held[p], got):
                changed = True
        return changed

    readers = {p: [] for p in prog.order}
    for q in prog.order:
        for s in deps[q]:
            readers[s].append(q)
    for comp in components(prog.order, deps):
        members = set(comp)
        pending = deque(comp)
        queued = set(comp)
        while pending:
            p = pending.popleft()
            queued.discard(p)
            if derive(p):
                for q in readers[p]:
                    if q in members and q not in queued:
                        queued.add(q)
                        pending.append(q)
    return tab
