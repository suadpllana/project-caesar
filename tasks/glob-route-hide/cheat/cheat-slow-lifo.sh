#!/bin/bash
# exact: sets over bindings, strongly connected components in order, but a last-in-first-out worklist inside each
set -euo pipefail

cat > /app/fe/vis.py <<'PYEOF'


def edge_level(ln, path):
    return 0 if ln.pb else dep(path)


def arriving(src_held, src, dst, lv):
    c = cpd(src, dst)
    got = {}
    for d, bits in src_held.items():
        if d <= c and bits:
            nd = max(d, lv)
            got[nd] = got.get(nd, 0) | bits
    return got


def absorb(into, got):
    changed = False
    for d, bits in got.items():
        wider = 0
        for e, b in into.items():
            if e <= d:
                wider |= b
        fresh = bits & ~wider
        if fresh:
            into[d] = into.get(d, 0) | fresh
            for e in list(into):
                if e > d:
                    into[e] &= ~fresh
                    if not into[e]:
                        del into[e]
            changed = True
    return changed


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
from fe import flag


def lines(prog, path):
    md = prog.mods.get(path)
    return [] if md is None else [ln for ln in md.lns
                                  if ln.k in ("item", "use") and flag.live(ln, prog.on)]


def names(prog, path):
    return {ln.nm if ln.k == "item" else ln.bn for ln in lines(prog, path)}
PYEOF

cat > /app/fe/glob.py <<'PYEOF'
from fe import flag


def lines(prog, path):
    md = prog.mods.get(path)
    return [] if md is None else [ln for ln in md.lns
                                  if ln.k == "glob" and flag.live(ln, prog.on)]
PYEOF

cat > /app/fe/fix.py <<'PYEOF'
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
        pending = list(comp)
        queued = set(comp)
        while pending:
            p = pending.pop()
            queued.discard(p)
            if derive(p):
                for q in readers[p]:
                    if q in members and q not in queued:
                        queued.add(q)
                        pending.append(q)
    return tab
PYEOF

cat > /app/fe/say.py <<'PYEOF'
def line(prog, tab, i):
    path, ref = prog.refs[i]
    name = ref.nm
    total = 0
    for bits in tab.held[path].values():
        total |= bits
    total &= tab.names.get(name, 0)
    got = [ix for ix in tab.under.get(name, ()) if total >> tab.slot[(ix, name)] & 1]
    got.sort()
    words = ["%s.%s" % (prog.items[ix][0], prog.items[ix][1].nm) for ix in got]
    if len(words) == 1:
        return "%s %s %s" % (path, name, words[0])
    if not words:
        return "%s %s %s" % (path, name, "broken" if name in tab.mine[path] else "unresolved")
    return "%s %s ambiguous %s" % (path, name, " ".join(words))
PYEOF

