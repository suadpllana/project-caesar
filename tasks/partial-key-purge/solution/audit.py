from db import drop, match

TOP = -1


def audit(store):
    """What `delete <table> <id>` of each row on its own would do, for every row at once.

    Replaying one delete per row costs the sum of all removed sets, which is quadratic on
    long revision chains. Instead:

    A row's cascade reference matches a set of rows, and the row goes exactly when all of
    them go. Outside loops, that makes "r removes v" the same as "every chain of matches that
    keeps v standing passes through r", so the rows a lone delete of r removes form r's
    subtree in one tree: v hangs under the lowest common owner of the rows it matches. Rows
    that match themselves, and rows on a loop of mutual matches, can never be removed by a
    delete of anything else, so they hang from the top; a loop member's own delete can take
    other members with it, and only those deletes are replayed. Rows of a table with two or
    more cascade references are never referenced, so they sit outside the tree: such a row
    goes when r owns all the matches of any one of its references, which is a union of
    chains towards the top.

    Every other effect of a lone delete of r is a question of the form "is r above y and
    above none of a few other nodes", which is answered for every r at once by signed marks
    summed over subtrees, with the unions of chains counted by inclusion and exclusion."""
    bk = match.book(store)
    rows = []
    at = {}
    for tab in store.script.tabs:
        for rid in store.ids(tab.name):
            at[(tab.name, rid)] = len(rows)
            rows.append((tab, rid))
    n = len(rows)

    gid = {}
    members = []

    def group(ref, pat, vals):
        slot = (ref.key.name, pat, tuple(vals[ref.cols[i]] for i in pat))
        g = gid.get(slot)
        if g is None:
            g = gid[slot] = len(members)
            kt = ref.key.tab.name
            members.append([at[(kt, p)] for p in bk.ups(ref, vals, pat)])
        return g

    links = [None] * n
    casc = [None] * n
    for v, (tab, rid) in enumerate(rows):
        vals = store.get(tab.name, rid)
        mine = []
        cs = []
        for ref in tab.refs:
            pat = match.form(ref, vals)
            g = group(ref, pat, vals) if pat else None
            mine.append((ref, g))
            if ref.act == "cascade" and g is not None and members[g]:
                cs.append(g)
        links[v] = mine
        casc[v] = cs

    ring = loops(n, casc, members)
    parent, order, lift = owners(n, casc, members, ring)
    lca = lift.lca

    meet = {}

    def x(g):
        got = meet.get(g)
        if got is None:
            got = None
            for m in members[g]:
                got = m if got is None else lca(got, m)
                if got == TOP:
                    break
            meet[g] = got
        return got

    size = [0] * n
    gone = [0] * n
    wipe = [0] * n
    held = [0] * n
    for v in range(n):
        if len(casc[v]) <= 1:
            size[v] = 1
        else:
            chains(gone, lca, [x(g) for g in casc[v]], 1)

    for v, (tab, rid) in enumerate(rows):
        vals = store.get(tab.name, rid)
        mine = links[v]
        mover = [x(g) for g in casc[v]] if len(casc[v]) > 1 else [v]
        for ref, g in mine:
            if ref.act == "restrict" and g is not None and members[g]:
                y = x(g)
                if y != TOP:
                    held[y] += 1
        sets = []
        for ref, g in mine:
            if ref.act == "setnull" and g is not None and members[g]:
                y = x(g)
                if y != TOP:
                    sets.append((ref, y))
        if sets:
            chains(wipe, lca, [y for _, y in sets], 1)
            chains(wipe, lca, [lca(y, m) for _, y in sets for m in mover], -1)
        for mask in range(1 << len(sets)):
            on = [sets[i] for i in range(len(sets)) if mask >> i & 1]
            off = [sets[i][1] for i in range(len(sets)) if not mask >> i & 1]
            top = None
            for _, y in on:
                top = y if top is None else lca(top, y)
            if top == TOP:
                continue
            now = list(vals)
            for ref, _ in on:
                for col in ref.wipe:
                    now[col] = None
            avoid = off + mover
            always = any(now[c] is None for key in tab.keys for c in key.cols)
            needs = []
            for ref, _ in mine:
                pat = match.form(ref, now)
                if pat is None:
                    continue
                if pat is False:
                    always = True
                    continue
                if not on and ref.act != "noaction":
                    continue
                if not bk.ups(ref, now, pat):
                    always = True
                    continue
                needs.append(x(group(ref, pat, now)))
            if always:
                if top is not None:
                    fence(held, lca, top, avoid)
                continue
            for y in needs:
                if y == TOP:
                    continue
                fence(held, lca, y if top is None else lca(top, y), avoid)

    for v in reversed(order):
        p = parent[v]
        if p != TOP:
            size[p] += size[v]
            gone[p] += gone[v]
            wipe[p] += wipe[v]
            held[p] += held[v]

    out = []
    for v, (tab, rid) in enumerate(rows):
        if v in ring or len(casc[v]) > 1:
            eff = drop.plan(store, tab.name, [rid])
            out.append((tab.name, rid, len(eff.gone), len(eff.new), eff.fail is not None))
        else:
            out.append((tab.name, rid, size[v] + gone[v], wipe[v], held[v] > 0))
    return out


def chains(marks, lca, tops, sign):
    """Add `sign` on every node above any of `tops`, by inclusion and exclusion over the
    lowest common owners of each subset."""
    tops = [t for t in set(tops) if t != TOP]
    k = len(tops)
    for mask in range(1, 1 << k):
        y = None
        bits = 0
        for i in range(k):
            if mask >> i & 1:
                bits += 1
                y = tops[i] if y is None else lca(y, tops[i])
                if y == TOP:
                    break
        if y != TOP:
            marks[y] += sign if bits % 2 else -sign


def fence(marks, lca, y, avoid):
    """Add one on every node above y that is above none of `avoid`."""
    if y == TOP:
        return
    marks[y] += 1
    chains(marks, lca, [lca(y, a) for a in avoid], -1)


def loops(n, casc, members):
    """Rows on a loop of two or more rows that match one another through cascade references,
    found as strongly connected components (Kosaraju, iteratively) of the graph that runs
    from a row through its match set to each row in it. A row that matches itself is left
    out: it hangs from the top on its own account."""
    groups = len(members)
    nodes = n + groups
    fwd = [[] for _ in range(nodes)]
    for v in range(n):
        if len(casc[v]) == 1 and v not in members[casc[v][0]]:
            fwd[v].append(n + casc[v][0])
    for g in range(groups):
        fwd[n + g] = members[g]
    back = [[] for _ in range(nodes)]
    for a in range(nodes):
        for b in fwd[a]:
            back[b].append(a)
    seen = [False] * nodes
    finish = []
    for s in range(nodes):
        if seen[s]:
            continue
        seen[s] = True
        stack = [(s, 0)]
        while stack:
            a, i = stack[-1]
            if i < len(fwd[a]):
                stack[-1] = (a, i + 1)
                b = fwd[a][i]
                if not seen[b]:
                    seen[b] = True
                    stack.append((b, 0))
            else:
                stack.pop()
                finish.append(a)
    comp = [-1] * nodes
    ring = set()
    for s in reversed(finish):
        if comp[s] != -1:
            continue
        comp[s] = s
        part = [s]
        stack = [s]
        while stack:
            a = stack.pop()
            for b in back[a]:
                if comp[b] == -1:
                    comp[b] = s
                    part.append(b)
                    stack.append(b)
        real = [a for a in part if a < n]
        if len(real) > 1:
            ring.update(real)
    return ring


def owners(n, casc, members, ring):
    """Owner of every row, and an order with every owner before what it owns.

    A row waits on its cascade match set; the set's owner is the lowest common owner of
    its rows, known once all of them are placed. Rows with no cascade reference, rows that
    match themselves and loop members hang from the top, and so do rows with two or more
    cascade references, which nothing references."""
    parent = [TOP] * n
    order = []
    waiting = {}
    left = {}
    meet = {}
    of = {}
    ready = []
    for v in range(n):
        if len(casc[v]) == 1 and v not in ring and v not in members[casc[v][0]]:
            g = casc[v][0]
            if g not in left:
                left[g] = len(members[g])
                for m in members[g]:
                    of.setdefault(m, []).append(g)
            waiting.setdefault(g, []).append(v)
        else:
            ready.append(v)
    lift = Lift(parent)
    while ready:
        v = ready.pop()
        order.append(v)
        lift.place(v)
        for g in of.get(v, ()):
            meet[g] = v if g not in meet else lift.lca(meet[g], v)
            left[g] -= 1
            if left[g] == 0:
                for w in waiting[g]:
                    parent[w] = meet[g]
                    ready.append(w)
    return parent, order, lift


class Lift:
    """Binary lifting over the owner tree, filled in as rows are placed top down."""

    def __init__(self, parent):
        self.parent = parent
        self.depth = [0] * len(parent)
        self.jump = [[TOP] * len(parent)]

    def place(self, v):
        p = self.parent[v]
        self.depth[v] = 0 if p == TOP else self.depth[p] + 1
        self.jump[0][v] = p
        k = 1
        while True:
            below = self.jump[k - 1][v]
            if below == TOP:
                up = TOP
            else:
                up = self.jump[k - 1][below]
            if k == len(self.jump):
                if up == TOP:
                    break
                self.jump.append([TOP] * len(self.parent))
            self.jump[k][v] = up
            if up == TOP:
                break
            k += 1

    def lca(self, a, b):
        if a == TOP or b == TOP:
            return TOP
        da, db = self.depth[a], self.depth[b]
        if da < db:
            a, b, da, db = b, a, db, da
        diff = da - db
        k = 0
        while diff:
            if diff & 1:
                a = self.jump[k][a]
            diff >>= 1
            k += 1
        if a == b:
            return a
        for k in range(len(self.jump) - 1, -1, -1):
            ja, jb = self.jump[k][a], self.jump[k][b]
            if ja != jb:
                a, b = ja, jb
        a, b = self.jump[0][a], self.jump[0][b]
        return a if a == b else TOP
