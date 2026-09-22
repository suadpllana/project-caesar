from db import drop, match

SMALL = 2000


def audit(store):
    rows = [(t.name, rid) for t in store.script.tabs for rid in store.ids(t.name)]
    if len(rows) <= SMALL:
        out = []
        for t, rid in rows:
            gone, new, bad = drop.outcome(store, t, [rid])
            out.append((t, rid, len(gone), len(new), bad is not None))
        return out
    return Fast(store, rows).run()


class Fast:
    def __init__(self, store, rows):
        self.store = store
        self.idx = match.ix(store)
        self.rows = rows
        self.node = {r: i + 1 for i, r in enumerate(rows)}
        self.n = len(rows)
        self.slots = {}
        self.sets = []

    def group(self, ref, vals):
        pat = match.shape(ref, vals)
        if not pat:
            return pat
        k = (ref.key.name, pat, tuple(vals[ref.cols[i]] for i in pat))
        if k not in self.slots:
            self.slots[k] = len(self.sets)
            kt = ref.key.tab.name
            self.sets.append([self.node[(kt, p)] for p in self.idx.parents(ref, pat, vals)])
        return self.slots[k]

    def run(self):
        store, n = self.store, self.n
        live = [None] * (n + 1)
        casc = [()] * (n + 1)
        for v in range(1, n + 1):
            t, rid = self.rows[v - 1]
            vals = store.get(t, rid)
            mine = [(ref, self.group(ref, vals)) for ref in store.tabs[t].refs]
            live[v] = mine
            casc[v] = tuple(g for ref, g in mine
                            if ref.act == "cascade" and g is not None and g is not False and self.sets[g])
        selfm = set()
        edges = [[] for _ in range(n + 1)]
        for v in range(1, n + 1):
            if len(casc[v]) == 1:
                if v in self.sets[casc[v][0]]:
                    selfm.add(v)
                else:
                    edges[v] = self.sets[casc[v][0]]
        ring = tarjan(n, edges)
        joins = {}
        for v in range(1, n + 1):
            if len(casc[v]) == 1 and v not in ring and v not in selfm:
                g = casc[v][0]
                if len(self.sets[g]) > 1 and g not in joins:
                    joins[g] = n + 1 + len(joins)
        total = n + len(joins)
        preds = [()] * (total + 1)
        roots = []
        for v in range(1, n + 1):
            if len(casc[v]) == 1 and v not in ring and v not in selfm:
                g = casc[v][0]
                preds[v] = (joins[g],) if g in joins else tuple(self.sets[g])
            elif len(casc[v]) <= 1:
                roots.append(v)
        for g, j in joins.items():
            preds[j] = tuple(self.sets[g])
        idom = chk(total, preds, roots)
        for v in range(1, n + 1):
            if len(casc[v]) > 1:
                idom[v] = 0
        tree = Euler(total, idom)
        lca = tree.lca
        tops = {}

        def top(g):
            if g not in tops:
                a = -1
                for m in self.sets[g]:
                    a = m if a == -1 else lca(a, m)
                    if a == 0:
                        break
                tops[g] = a
            return tops[g]

        gm = [0] * (total + 1)
        wm = [0] * (total + 1)
        hm = [0] * (total + 1)
        tin = tree.tin

        def union(marks, ts, sign):
            ts = sorted({t for t in ts if t > 0}, key=tin.__getitem__)
            for i, t in enumerate(ts):
                marks[t] += sign
                if i:
                    a = lca(ts[i - 1], t)
                    if a > 0:
                        marks[a] -= sign

        def minus(marks, y, avoid):
            if y is not None and y > 0:
                marks[y] += 1
                union(marks, [lca(y, a) for a in avoid], -1)

        size = [0] * (total + 1)
        for v in range(1, n + 1):
            if len(casc[v]) > 1:
                union(gm, [top(g) for g in casc[v]], 1)
            else:
                size[v] = 1
        for v in range(1, n + 1):
            t, rid = self.rows[v - 1]
            vals = store.get(t, rid)
            mine = live[v]
            dt = [top(g) for g in casc[v]] if len(casc[v]) > 1 else [v]
            for ref, g in mine:
                if ref.act == "restrict" and g is not None and g is not False and self.sets[g]:
                    y = top(g)
                    if y > 0:
                        hm[y] += 1
            sn = [(ref, top(g)) for ref, g in mine
                  if ref.act == "setnull" and g is not None and g is not False and self.sets[g]]
            sn = [(ref, y) for ref, y in sn if y > 0]
            if sn:
                union(wm, [y for _, y in sn], 1)
                union(wm, [lca(y, a) for _, y in sn for a in dt], -1)
            for mask in range(1 << len(sn)):
                on = [sn[i] for i in range(len(sn)) if mask >> i & 1]
                off = [sn[i][1] for i in range(len(sn)) if not mask >> i & 1]
                ys = None
                for _, y in on:
                    ys = y if ys is None else lca(ys, y)
                if ys == 0:
                    continue
                now = list(vals)
                for ref, _ in on:
                    for c in ref.wipe:
                        now[c] = None
                every = any(now[c] is None for key in store.tabs[t].keys for c in key.cols)
                conds = []
                for ref, _ in mine:
                    pat = match.shape(ref, now)
                    if pat is None:
                        continue
                    if pat is False:
                        every = True
                        continue
                    if not on and ref.act != "noaction":
                        continue
                    if not self.idx.parents(ref, pat, now):
                        every = True
                        continue
                    conds.append(top(self.group(ref, now)))
                if every:
                    if ys is not None:
                        minus(hm, ys, off + dt)
                    continue
                for xc in conds:
                    if xc > 0:
                        minus(hm, xc if ys is None else lca(ys, xc), off + dt)
        order = sorted(range(total + 1), key=tin.__getitem__)

        def sums(marks):
            pre = [0]
            for v in order:
                pre.append(pre[-1] + marks[v])
            return [pre[tree.tout[v] + 1] - pre[tin[v]] for v in range(n + 1)]

        gs, ws, hs, ss = sums(gm), sums(wm), sums(hm), sums(size)
        out = []
        for v in range(1, n + 1):
            t, rid = self.rows[v - 1]
            if v in ring or len(casc[v]) > 1:
                gone, new, bad = drop.outcome(store, t, [rid])
                out.append((t, rid, len(gone), len(new), bad is not None))
            else:
                out.append((t, rid, ss[v] + gs[v], ws[v], hs[v] > 0))
        return out


def chk(n, preds, roots):
    succ = [[] for _ in range(n + 1)]
    succ[0] = list(roots)
    for v in range(1, n + 1):
        for p in preds[v]:
            succ[p].append(v)
    post = [-1] * (n + 1)
    order = []
    seen = [False] * (n + 1)
    seen[0] = True
    stack = [(0, 0)]
    while stack:
        v, i = stack.pop()
        if i < len(succ[v]):
            stack.append((v, i + 1))
            w = succ[v][i]
            if not seen[w]:
                seen[w] = True
                stack.append((w, 0))
        else:
            post[v] = len(order)
            order.append(v)
    rootset = set(roots)
    ps = [sorted(p, key=post.__getitem__) if len(p) > 1 else p for p in preds]
    idom = [-1] * (n + 1)
    idom[0] = 0
    changed = True
    while changed:
        changed = False
        for v in reversed(order):
            if v == 0:
                continue
            new = -1
            for p in ((0,) if v in rootset else ps[v]):
                if idom[p] == -1:
                    continue
                if new == -1:
                    new = p
                    continue
                a, b = p, new
                while a != b:
                    while post[a] < post[b]:
                        a = idom[a]
                    while post[b] < post[a]:
                        b = idom[b]
                new = a
            if idom[v] != new:
                idom[v] = new
                changed = True
    return idom


def tarjan(n, edges):
    index = [0] * (n + 1)
    low = [0] * (n + 1)
    on = [False] * (n + 1)
    st = []
    out = set()
    c = 1
    for s in range(1, n + 1):
        if index[s]:
            continue
        index[s] = low[s] = c
        c += 1
        st.append(s)
        on[s] = True
        call = [(s, 0)]
        while call:
            v, i = call[-1]
            if i < len(edges[v]):
                call[-1] = (v, i + 1)
                w = edges[v][i]
                if not index[w]:
                    index[w] = low[w] = c
                    c += 1
                    st.append(w)
                    on[w] = True
                    call.append((w, 0))
                elif on[w]:
                    low[v] = min(low[v], index[w])
            else:
                call.pop()
                if call:
                    u = call[-1][0]
                    low[u] = min(low[u], low[v])
                if low[v] == index[v]:
                    comp = []
                    while True:
                        w = st.pop()
                        on[w] = False
                        comp.append(w)
                        if w == v:
                            break
                    if len(comp) > 1:
                        out.update(comp)
    return out


class Euler:
    def __init__(self, n, idom):
        kids = [[] for _ in range(n + 1)]
        for v in range(1, n + 1):
            kids[idom[v]].append(v)
        self.tin = [0] * (n + 1)
        self.tout = [0] * (n + 1)
        self.depth = [0] * (n + 1)
        self.first = [0] * (n + 1)
        tour = []
        clock = 0
        stack = [(0, 0)]
        while stack:
            v, i = stack.pop()
            if i == 0:
                self.tin[v] = clock
                clock += 1
                self.first[v] = len(tour)
            tour.append(v)
            if i < len(kids[v]):
                stack.append((v, i + 1))
                w = kids[v][i]
                self.depth[w] = self.depth[v] + 1
                stack.append((w, 0))
            else:
                self.tout[v] = clock - 1
        depth = self.depth
        self.sp = [tour]
        j = 1
        while 2 * j <= len(tour):
            prev = self.sp[-1]
            self.sp.append([prev[i] if depth[prev[i]] <= depth[prev[i + j]] else prev[i + j]
                            for i in range(len(tour) - 2 * j + 1)])
            j *= 2

    def lca(self, a, b):
        i, j = self.first[a], self.first[b]
        if i > j:
            i, j = j, i
        k = (j - i + 1).bit_length() - 1
        x, y = self.sp[k][i], self.sp[k][j - (1 << k) + 1]
        return x if self.depth[x] <= self.depth[y] else y
