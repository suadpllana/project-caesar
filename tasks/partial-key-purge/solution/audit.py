from db import hold, match


def audit(store):
    """What `delete <table> <id>` of each row on its own would do, for every row at once.

    Replaying one delete per row costs the sum of all removed sets, which is quadratic on long
    revision histories. The audit turns the question round: for every row v it works out the
    set of rows whose lone delete removes v - its deleters - and everything the audit prints is
    read off those sets.

    A row goes when every row it matched through one of its cascade references has gone, so its
    deleters are the row itself plus, for each cascade reference, the rows that are deleters of
    all its matches at once: a union over references of an intersection over matches. Neither a
    tree nor reachability describes that. Rows that match only one another keep each other, so
    on a loop the sets are the smallest ones the rule allows, grown from the row alone until
    they stop changing; a loop member with a cascade reference leading out of the loop can still
    be taken by what lies outside it. Sets are integers used as bit sets, one bit per row.

    The depth limit needs the round, not just the fact of removal: the rows whose lone delete
    removes v within fifteen rounds are built the same way one round at a time, and a deleter
    outside that set takes v too late. Counts are column sums over the deleter sets, done with
    bit-sliced counters. A refusal names the first declared failing key or reference and then
    the smallest failing id, which is a minimum, not a sum: failures are visited in that order
    and each deleter keeps the first one that reaches it."""
    bk = match.book(store)
    rows = []
    at = {}
    for tab in store.script.tabs:
        for rid in store.ids(tab.name):
            at[(tab.name, rid)] = len(rows)
            rows.append((tab, rid))
    n = len(rows)
    one = [1 << v for v in range(n)]

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
            if pat:
                g = group(ref, pat, vals)
                mine.append((ref, g))
                if ref.act == "cascade" and members[g]:
                    cs.append(g)
        links[v] = mine
        casc[v] = cs

    kill, meets = deleters(n, casc, members, one)
    soon = early(n, casc, members, one, hold.LIMIT)

    def meet(g):
        got = meets.get(g)
        if got is None:
            ms = members[g]
            if not ms:
                got = 0
            else:
                got = kill[ms[0]]
                for u in ms[1:]:
                    got &= kill[u]
                    if not got:
                        break
            meets[g] = got
        return got

    gone = Tally()
    for v in range(n):
        gone.add(kill[v])
    wiped = Tally()
    for v in range(n):
        lost = 0
        for ref, g in links[v]:
            if ref.act == "setnull":
                lost |= meet(g)
        lost &= ~kill[v]
        if lost:
            wiped.add(lost)

    named = [None] * n
    todo = (1 << n) - 1
    tabs = {t.name: t for t in store.script.tabs}
    for decl in store.script.decls:
        tab = tabs[decl.tab.name]
        is_ref = hasattr(decl, "act")
        for rid in store.ids(tab.name):
            v = at[(tab.name, rid)]
            if is_ref:
                hit = fails_ref(store, bk, decl, v, rid, links[v], kill[v], soon, meet, group)
            else:
                hit = fails_key(store, decl, v, rid, links[v], kill[v], meet)
            hit &= todo
            if hit:
                todo ^= hit
                while hit:
                    low = hit & -hit
                    named[low.bit_length() - 1] = (decl.name, rid)
                    hit ^= low
        if not todo:
            break

    removed = gone.counts(n)
    cleared = wiped.counts(n)
    return [(tab.name, rid, removed[v], cleared[v], named[v])
            for v, (tab, rid) in enumerate(rows)]


def fired(store, rid, tab, links, kill_v, meet):
    """The ways a remaining row can be cleared: for each non-empty set of its setnull
    references, the deleters that clear exactly those and remove nothing of the row, and the
    row's values once they are cleared."""
    sets = [(ref, meet(g)) for ref, g in links if ref.act == "setnull"]
    if not sets:
        return []
    vals = store.get(tab.name, rid)
    out = []
    for mask in range(1, 1 << len(sets)):
        where = ~kill_v
        now = list(vals)
        for i, (ref, lost) in enumerate(sets):
            if mask >> i & 1:
                where &= lost
                for c in ref.wipe:
                    now[c] = None
            else:
                where &= ~lost
            if not where:
                break
        if where:
            out.append((where, now))
    return out


def fails_ref(store, bk, ref, v, rid, links, kill_v, soon, meet, group):
    """Deleters whose lone delete makes row v fail reference `ref`."""
    tab = ref.tab
    g = None
    for r, gg in links:
        if r is ref:
            g = gg
    hit = 0
    if g is not None:
        lost = meet(g)
        if ref.act == "restrict":
            hit |= lost
        elif ref.act == "cascade":
            hit |= lost & ~soon[v]
        elif ref.act == "noaction":
            clear = 0
            for r, gg in links:
                if r.act == "setnull":
                    clear |= meet(gg)
            hit |= lost & ~kill_v & ~clear
    for where, now in fired(store, rid, tab, links, kill_v, meet):
        pat = match.form(ref, now)
        if pat is None:
            continue
        if pat is False:
            hit |= where
            continue
        g2 = group(ref, pat, now)
        hit |= where if not bk.ups(ref, now, pat) else where & meet(g2)
    return hit


def fails_key(store, key, v, rid, links, kill_v, meet):
    """Deleters whose lone delete leaves row v with a null in a column of `key`."""
    hit = 0
    for where, now in fired(store, rid, key.tab, links, kill_v, meet):
        if any(now[c] is None for c in key.cols):
            hit |= where
    return hit


def deleters(n, casc, members, one):
    """Deleter set of every row and every match set, as the smallest sets the rule allows.

    Rows and match sets form one graph, from a row to the match sets of its cascade references
    and from a match set to its rows. Its strongly connected components (Tarjan, iteratively)
    come out with everything a component depends on before it, so a component that is a single
    row or match set is settled in one step; a loop is grown from each row alone until nothing
    changes, which gives the smallest sets."""
    groups = len(members)
    nodes = n + groups
    adj = [None] * nodes
    for v in range(n):
        adj[v] = [n + g for g in casc[v]]
    for g in range(groups):
        adj[n + g] = members[g]
    kill = [0] * n
    meets = {}

    def settle(x):
        if x < n:
            got = one[x]
            for g in casc[x]:
                got |= meets.get(g, 0)
            return got
        ms = members[x - n]
        if not ms:
            return 0
        got = kill[ms[0]]
        for u in ms[1:]:
            got &= kill[u]
            if not got:
                break
        return got

    index = [-1] * nodes
    low = [0] * nodes
    onst = [False] * nodes
    stack = []
    clock = 0
    for s in range(nodes):
        if index[s] != -1:
            continue
        index[s] = low[s] = clock
        clock += 1
        stack.append(s)
        onst[s] = True
        work = [(s, 0)]
        while work:
            x, i = work[-1]
            nb = adj[x]
            if i < len(nb):
                work[-1] = (x, i + 1)
                y = nb[i]
                if index[y] == -1:
                    index[y] = low[y] = clock
                    clock += 1
                    stack.append(y)
                    onst[y] = True
                    work.append((y, 0))
                elif onst[y] and index[y] < low[x]:
                    low[x] = index[y]
                continue
            work.pop()
            if work:
                p = work[-1][0]
                if low[x] < low[p]:
                    low[p] = low[x]
            if low[x] != index[x]:
                continue
            part = []
            while True:
                y = stack.pop()
                onst[y] = False
                part.append(y)
                if y == x:
                    break
            if len(part) == 1:
                if x < n:
                    kill[x] = settle(x)
                else:
                    meets[x - n] = settle(x)
                continue
            for y in part:
                if y < n:
                    kill[y] = one[y]
                else:
                    meets[y - n] = 0
            moved = True
            while moved:
                moved = False
                for y in part:
                    got = settle(y)
                    if y < n:
                        if got != kill[y]:
                            kill[y] = got
                            moved = True
                    elif got != meets[y - n]:
                        meets[y - n] = got
                        moved = True
    return kill, meets


def early(n, casc, members, one, limit):
    """For every row, the rows whose lone delete removes it within `limit` rounds: round by
    round, a row is taken in round k by the rows that take every row it matched through one of
    its cascade references in round k - 1 or sooner."""
    cur = list(one)
    for _ in range(limit):
        nxt = list(cur)
        memo = {}
        for v in range(n):
            cs = casc[v]
            if not cs:
                continue
            got = one[v]
            for g in cs:
                m = memo.get(g)
                if m is None:
                    ms = members[g]
                    m = cur[ms[0]]
                    for u in ms[1:]:
                        m &= cur[u]
                        if not m:
                            break
                    memo[g] = m
                got |= m
            nxt[v] = got
        cur = nxt
    return cur


class Tally:
    """Column sums of many bit sets, kept as bit-sliced binary counters."""

    def __init__(self):
        self.digits = []

    def add(self, bits):
        digits = self.digits
        i = 0
        while bits:
            if i == len(digits):
                digits.append(bits)
                return
            d = digits[i]
            digits[i] = d ^ bits
            bits &= d
            i += 1

    def counts(self, n):
        out = [0] * n
        for i, d in enumerate(self.digits):
            s = bin(d)[:1:-1]
            w = 1 << i
            for v in range(min(n, len(s))):
                if s[v] == "1":
                    out[v] += w
        return out
