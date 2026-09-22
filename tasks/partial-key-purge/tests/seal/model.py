"""Sealed model of the row store. Root-only at grading time; never importable by agent code.

Written apart from the reference in `solution/`, and checked against a brute-force transcription
of the contract on generated stores before anything was frozen. It reads scripts itself rather
than through the shipped reader, so a change to the shipped tree cannot move it.

Deletes: the removed set is grown from the named rows with a count of surviving matches per
(row, reference); a row whose cascade count reaches zero is removed and its own referrers are
counted down in turn. That is the smallest set closed under the rule, because nothing is ever
removed without every row it matched being removed first. Matching reads the values from before
the statement. Only rows that lost a reference, and rows that matched a row whose key column was
cleared, can fail the end state, so only they are checked.

Audit: for a row outside every loop of cascade matches, the rows a lone delete removes are
exactly the rows it dominates in the flow graph whose edges run from each matched row to the row
matching it, with loop members detached as roots (a loop keeps itself against any outside
delete) and rows with two or more live cascade references (never referenced, by contract) kept
out of the graph. Dominators come from the iterative two-finger algorithm over reverse
postorder; ancestors are tested on an Euler tour with a sparse table. Every other effect of a
lone delete of r is a question "is r an ancestor of y and of none of a few other nodes", which is
answered for all r at once with signed marks summed over subtrees. A match set shared by
several rows enters the flow graph once, as a join node between its rows and the rows that
match it, so the graph stays linear in the store. A row that matches itself
through its cascade reference is a root too: nothing outside it can ever remove it, and what a
delete of it removes is its subtree. Members of loops of two or more rows are replayed.
"""

EMPTY = ()


class DB:
    def __init__(self, text):
        self.order = []
        self.cols = {}
        self.keys = {}
        self.refs = {}
        self.decls = []
        self.data = {}
        self.stmts = []
        for raw in text.split("\n"):
            w = raw.split()
            if not w or w[0].startswith("#"):
                continue
            op = w[0]
            if op == "table":
                self.order.append(w[1])
                self.cols[w[1]] = w[2:]
                self.data[w[1]] = {}
            elif op == "key":
                ix = [self.cols[w[2]].index(c) for c in w[3:]]
                self.keys[w[1]] = (w[2], tuple(ix), len(self.decls))
                self.decls.append(w[1])
            elif op == "ref":
                a = w.index("->")
                ix = tuple(self.cols[w[2]].index(c) for c in w[3:a])
                act = w[a + 3]
                wipe = tuple(self.cols[w[2]].index(c) for c in w[a + 4:]) or ix
                self.refs[w[1]] = {
                    "name": w[1], "tab": w[2], "cols": ix, "key": w[a + 1],
                    "ktab": self.keys[w[a + 1]][0], "kcols": self.keys[w[a + 1]][1],
                    "mode": w[a + 2], "act": act,
                    "wipe": wipe if act == "setnull" else EMPTY, "pos": len(self.decls)}
                self.decls.append(w[1])
            elif op == "row":
                self.data[w[1]][int(w[2])] = tuple(None if v == "-" else v for v in w[3:])
            elif op == "delete":
                self.stmts.append(("delete", w[1], [int(x) for x in w[2:]]))
            elif op == "dump":
                self.stmts.append(("dump", w[1], None))
            else:
                self.stmts.append(("audit", None, None))
        self.out_refs = {t: [r for r in self.refs.values() if r["tab"] == t] for t in self.order}
        self.in_refs = {t: [r for r in self.refs.values() if r["ktab"] == t] for t in self.order}
        self.tab_keys = {t: [(n, k[1], k[2]) for n, k in self.keys.items() if k[0] == t]
                         for t in self.order}


def shape(ref, vals):
    """None for inert, False for broken, else the positions of the non-null columns."""
    got = tuple(i for i, c in enumerate(ref["cols"]) if vals[c] is not None)
    if not got:
        return None
    if len(got) < len(ref["cols"]):
        if ref["mode"] == "simple":
            return None
        if ref["mode"] == "full":
            return False
    return got


class Index:
    """Value indexes over one fixed version of the data."""

    def __init__(self, db, data):
        self.db = db
        self.data = data
        self.up = {}
        self.down = {}

    def parents(self, ref, pat, vals):
        """Ids in ref's key table whose key agrees with vals on the positions in pat."""
        slot = (ref["key"], pat)
        idx = self.up.get(slot)
        if idx is None:
            idx = {}
            kc = [ref["kcols"][i] for i in pat]
            for pid, pv in self.data[ref["ktab"]].items():
                idx.setdefault(tuple(pv[c] for c in kc), []).append(pid)
            self.up[slot] = idx
        return idx.get(tuple(vals[ref["cols"][i]] for i in pat), EMPTY)

    def children(self, ref, pvals):
        """Live referrers of a key row with values pvals through ref."""
        idx = self.down.get(ref["name"])
        if idx is None:
            idx = {}
            for cid, cv in self.data[ref["tab"]].items():
                pat = shape(ref, cv)
                if pat:
                    idx.setdefault(pat, {}).setdefault(
                        tuple(cv[ref["cols"][i]] for i in pat), []).append(cid)
            self.down[ref["name"]] = idx
        out = []
        for pat, table in idx.items():
            hit = table.get(tuple(pvals[ref["kcols"][i]] for i in pat))
            if hit:
                out.extend(hit)
        return out


def attempt(db, ix, tab, ids):
    """(removed, cleared, failure) of `delete tab ids` over ix.data; nothing is changed."""
    data = ix.data
    gone = set((tab, i) for i in ids)
    work = list(gone)
    left = {}
    lost = []
    while work:
        pt, p = work.pop()
        pv = data[pt][p]
        for r in db.in_refs[pt]:
            ct = r["tab"]
            for c in ix.children(r, pv):
                slot = (ct, c, r["name"])
                n = left.get(slot)
                if n is None:
                    n = len(ix.parents(r, shape(r, data[ct][c]), data[ct][c]))
                n -= 1
                left[slot] = n
                if n == 0:
                    lost.append(slot)
                    if r["act"] == "cascade" and (ct, c) not in gone:
                        gone.add((ct, c))
                        work.append((ct, c))
    fails = []
    new = {}
    wiped = set()
    look = set()
    for ct, c, rn in lost:
        r = db.refs[rn]
        if r["act"] == "restrict":
            fails.append((r["pos"], c))
        if (ct, c) in gone:
            continue
        look.add((ct, c))
        if r["act"] == "setnull":
            vals = list(new.get((ct, c), data[ct][c]))
            for i in r["wipe"]:
                vals[i] = None
            new[(ct, c)] = tuple(vals)
            wiped.add((ct, c))
    moved = {}
    for (ct, c), vals in new.items():
        old = data[ct][c]
        for kn, kc, _ in db.tab_keys[ct]:
            if any(vals[i] != old[i] for i in kc):
                moved[(ct, c)] = vals
                for r in db.in_refs[ct]:
                    if r["key"] == kn:
                        for d in ix.children(r, old):
                            if (r["tab"], d) not in gone:
                                look.add((r["tab"], d))
    for ct, c in look:
        vals = new.get((ct, c), data[ct][c])
        for r in db.out_refs[ct]:
            pat = shape(r, vals)
            if pat is None:
                continue
            if pat is False:
                fails.append((r["pos"], c))
                continue
            ok = False
            for p in ix.parents(r, pat, vals):
                if (r["ktab"], p) in gone:
                    continue
                pv = moved.get((r["ktab"], p))
                if pv is not None and any(pv[r["kcols"][i]] is None for i in pat):
                    continue
                ok = True
                break
            if not ok:
                fails.append((r["pos"], c))
        for _, kc, kpos in db.tab_keys[ct]:
            if any(vals[i] is None for i in kc):
                fails.append((kpos, c))
    fail = None
    if fails:
        pos = min(f[0] for f in fails)
        fail = (db.decls[pos], min(f[1] for f in fails if f[0] == pos))
    return gone, wiped, new, fail


class Tree:
    """Dominator tree over node ids 0..n, rooted at 0, with O(1) ancestor tests and LCA."""

    def __init__(self, n, idom):
        kids = [[] for _ in range(n + 1)]
        for v in range(1, n + 1):
            kids[idom[v]].append(v)
        self.tin = [0] * (n + 1)
        self.tout = [0] * (n + 1)
        depth = [0] * (n + 1)
        first = [0] * (n + 1)
        euler = []
        clock = 0
        stack = [(0, 0)]
        while stack:
            v, i = stack.pop()
            if i == 0:
                self.tin[v] = clock
                clock += 1
                first[v] = len(euler)
            euler.append(v)
            if i < len(kids[v]):
                stack.append((v, i + 1))
                c = kids[v][i]
                depth[c] = depth[v] + 1
                stack.append((c, 0))
            else:
                self.tout[v] = clock - 1
        self.first = first
        self.depth = depth
        table = [euler]
        span = 1
        while 2 * span <= len(euler):
            prev = table[-1]
            cur = []
            for i in range(len(euler) - 2 * span + 1):
                a, b = prev[i], prev[i + span]
                cur.append(a if depth[a] <= depth[b] else b)
            table.append(cur)
            span *= 2
        self.table = table

    def lca(self, a, b):
        i, j = self.first[a], self.first[b]
        if i > j:
            i, j = j, i
        k = (j - i + 1).bit_length() - 1
        x, y = self.table[k][i], self.table[k][j - (1 << k) + 1]
        return x if self.depth[x] <= self.depth[y] else y


def dominators(n, preds, roots):
    """Iterative two-finger dominators on a flow graph from node 0."""
    succ = [[] for _ in range(n + 1)]
    for v in roots:
        succ[0].append(v)
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
    idom = [-1] * (n + 1)
    idom[0] = 0
    rpo = order[::-1]
    preds = [sorted(ps, key=post.__getitem__) if len(ps) > 1 else ps for ps in preds]
    changed = True
    while changed:
        changed = False
        for v in rpo:
            if v == 0:
                continue
            ps = [0] if v in roots else preds[v]
            new = -1
            for p in ps:
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


def loops(n, edges):
    """Nodes on a cycle of the graph (strongly connected with another node, or a self edge)."""
    index = [0] * (n + 1)
    low = [0] * (n + 1)
    onstack = [False] * (n + 1)
    stack = []
    out = set()
    counter = 1
    for s in range(1, n + 1):
        if index[s]:
            continue
        call = [(s, 0)]
        index[s] = low[s] = counter
        counter += 1
        stack.append(s)
        onstack[s] = True
        while call:
            v, i = call[-1]
            if i < len(edges[v]):
                call[-1] = (v, i + 1)
                w = edges[v][i]
                if not index[w]:
                    index[w] = low[w] = counter
                    counter += 1
                    stack.append(w)
                    onstack[w] = True
                    call.append((w, 0))
                elif onstack[w] and index[w] < low[v]:
                    low[v] = index[w]
            else:
                call.pop()
                if call:
                    u = call[-1][0]
                    if low[v] < low[u]:
                        low[u] = low[v]
                if low[v] == index[v]:
                    comp = []
                    while True:
                        w = stack.pop()
                        onstack[w] = False
                        comp.append(w)
                        if w == v:
                            break
                    if len(comp) > 1 or v in edges[v]:
                        out.update(comp)
    return out


def audit(db, ix):
    data = ix.data
    node = {}
    rows = []
    for t in db.order:
        for rid in sorted(data[t]):
            rows.append((t, rid))
            node[(t, rid)] = len(rows)
    n = len(rows)
    groups = {}
    gid = {}

    def group(r, vals):
        pat = shape(r, vals)
        if not pat:
            return pat
        slot = (r["key"], pat, tuple(vals[r["cols"][i]] for i in pat))
        g = gid.get(slot)
        if g is None:
            g = len(groups)
            gid[slot] = g
            groups[g] = [node[(r["ktab"], p)] for p in ix.parents(r, pat, vals)]
        return g

    live = [None] * (n + 1)
    casc = [EMPTY] * (n + 1)
    for v in range(1, n + 1):
        t, rid = rows[v - 1]
        vals = data[t][rid]
        mine = []
        cs = []
        for r in db.out_refs[t]:
            g = group(r, vals)
            mine.append((r, g))
            if r["act"] == "cascade" and g is not None and g is not False and groups[g]:
                cs.append(g)
        live[v] = mine
        casc[v] = tuple(cs)

    edges = [[] for _ in range(n + 1)]
    selfm = set()
    for v in range(1, n + 1):
        if len(casc[v]) == 1:
            if v in groups[casc[v][0]]:
                selfm.add(v)
            else:
                edges[v] = groups[casc[v][0]]
    ring = loops(n, edges)
    joins = {}
    for v in range(1, n + 1):
        if len(casc[v]) == 1 and v not in ring and v not in selfm:
            g = casc[v][0]
            if len(groups[g]) > 1 and g not in joins:
                joins[g] = n + 1 + len(joins)
    total = n + len(joins)
    preds = [EMPTY] * (total + 1)
    roots = set()
    for v in range(1, n + 1):
        if len(casc[v]) == 1 and v not in ring and v not in selfm:
            g = casc[v][0]
            preds[v] = (joins[g],) if g in joins else tuple(groups[g])
        elif len(casc[v]) <= 1:
            roots.add(v)
    for g, j in joins.items():
        preds[j] = tuple(groups[g])
    idom = dominators(total, preds, roots)
    for v in range(1, n + 1):
        if len(casc[v]) > 1:
            idom[v] = 0
    tree = Tree(total, idom)
    lca = tree.lca

    top = {}

    def x(g):
        got = top.get(g)
        if got is None:
            got = -1
            for m in groups[g]:
                got = m if got == -1 else lca(got, m)
                if got == 0:
                    break
            top[g] = got
        return got

    gone_m = [0] * (total + 1)
    wipe_m = [0] * (total + 1)
    held_m = [0] * (total + 1)
    tin = tree.tin

    def union(marks, tops, sign):
        ts = sorted(set(t for t in tops if t > 0), key=lambda t: tin[t])
        for i, t in enumerate(ts):
            marks[t] += sign
            if i:
                a = lca(ts[i - 1], t)
                if a > 0:
                    marks[a] -= sign

    def minus(marks, y, avoid):
        if y is None or y <= 0:
            return
        marks[y] += 1
        union(marks, [lca(y, a) for a in avoid], -1)

    size = [1] * (n + 1) + [0] * len(joins)
    size[0] = 0
    for v in range(1, n + 1):
        if len(casc[v]) > 1:
            size[v] = 0
            union(gone_m, [x(g) for g in casc[v]], 1)

    for v in range(1, n + 1):
        t, rid = rows[v - 1]
        vals = data[t][rid]
        mine = live[v]
        if len(casc[v]) > 1:
            dtops = [x(g) for g in casc[v]]
        else:
            dtops = [v]
        for r, g in mine:
            if r["act"] == "restrict" and g is not None and g is not False and groups[g]:
                xg = x(g)
                if xg > 0:
                    held_m[xg] += 1
        sets = [(r, x(g)) for r, g in mine
                if r["act"] == "setnull" and g is not None and g is not False and groups[g]]
        sets = [(r, xg) for r, xg in sets if xg > 0]
        if sets:
            tops = [xg for _, xg in sets]
            union(wipe_m, tops, 1)
            union(wipe_m, [lca(a, d) for a in tops for d in dtops], -1)
        for mask in range(1 << len(sets)):
            on = [sets[i] for i in range(len(sets)) if mask >> i & 1]
            off = [sets[i][1] for i in range(len(sets)) if not mask >> i & 1]
            ys = None
            for _, xg in on:
                ys = xg if ys is None else lca(ys, xg)
            if ys == 0:
                continue
            new = list(vals)
            for r, _ in on:
                for i in r["wipe"]:
                    new[i] = None
            avoid = off + dtops
            always = False
            for _, kc, _ in db.tab_keys[t]:
                if any(new[i] is None for i in kc):
                    always = True
            conds = []
            for r, g in mine:
                pat = shape(r, new)
                if pat is None:
                    continue
                if pat is False:
                    always = True
                    continue
                if not on and r["act"] != "noaction":
                    continue
                hits = ix.parents(r, pat, new)
                if not hits:
                    always = True
                    continue
                g2 = group(r, new)
                conds.append(x(g2))
            if always:
                if ys is not None:
                    minus(held_m, ys, avoid)
                continue
            for xc in conds:
                if xc <= 0:
                    continue
                y = xc if ys is None else lca(ys, xc)
                minus(held_m, y, avoid)

    order = sorted(range(total + 1), key=lambda v: tin[v])

    def sums(marks):
        pre = [0] * (total + 2)
        for i, v in enumerate(order):
            pre[i + 1] = pre[i] + marks[v]
        return [pre[tree.tout[v] + 1] - pre[tin[v]] for v in range(n + 1)]

    gone_s = sums(gone_m)
    wipe_s = sums(wipe_m)
    held_s = sums(held_m)
    size_s = sums(size)
    out = []
    for v in range(1, n + 1):
        t, rid = rows[v - 1]
        if v in ring:
            gone, wiped, _, fail = attempt(db, ix, t, [rid])
            out.append((t, rid, len(gone), len(wiped), fail is not None))
        elif len(casc[v]) > 1:
            gone, wiped, _, fail = attempt(db, ix, t, [rid])
            out.append((t, rid, len(gone), len(wiped), fail is not None))
        else:
            out.append((t, rid, size_s[v] + gone_s[v], wipe_s[v], held_s[v] > 0))
    return out


def expect(text):
    db = DB(text)
    data = {t: dict(rows) for t, rows in db.data.items()}
    ix = Index(db, data)
    out = []
    for op, tab, ids in db.stmts:
        if op == "delete":
            gone, wiped, new, fail = attempt(db, ix, tab, ids)
            if fail is not None:
                out.append("refused %s %d" % fail)
                continue
            data = {t: dict(rows) for t, rows in data.items()}
            for t, rid in gone:
                del data[t][rid]
            for (t, rid), vals in new.items():
                data[t][rid] = vals
            ix = Index(db, data)
            out.append("ok %d %d" % (len(gone), len(wiped)))
        elif op == "dump":
            for rid in sorted(data[tab]):
                vals = ["-" if v is None else v for v in data[tab][rid]]
                out.append(" ".join([tab, str(rid)] + vals))
        else:
            for t, rid, gone, wiped, held in audit(db, ix):
                out.append("%s %d %d %d %s" % (t, rid, gone, wiped, "held" if held else "ok"))
    return out


if __name__ == "__main__":
    import sys
    sys.stdout.write("".join(line + "\n" for line in expect(open(sys.argv[1]).read())))
