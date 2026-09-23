#!/bin/bash
# wrong reading loops-always-keep: the reference with this reading's files
set -euo pipefail

cat > /app/db/match.py <<'PYEOF'
def form(ref, vals):
    """How a row's values stand against a reference: None when the reference is inert for
    them, False when it is broken (full, some columns null but not all), and otherwise the
    positions within the reference's columns that carry a value, which are the positions a
    matched key row has to agree on."""
    got = tuple(i for i, c in enumerate(ref.cols) if vals[c] is not None)
    if not got:
        return None
    if len(got) < len(ref.cols):
        if ref.mode == "simple":
            return None
        if ref.mode == "full":
            return False
    return got


class Book:
    """Value indexes over the store as it stands. A partial reference can leave any subset
    of its columns null, so rows are indexed once per pattern of non-null positions: key
    rows by the projection of their key onto the pattern, referencing rows by the projection
    of their own values. Built lazily and thrown away whenever the store changes."""

    def __init__(self, store):
        self.store = store
        self.up = {}
        self.down = {}

    def ups(self, ref, vals, pat=None):
        """Ids of the key rows that `vals` matches through `ref`."""
        if pat is None:
            pat = form(ref, vals)
            if not pat:
                return ()
        slot = (ref.key.name, pat)
        idx = self.up.get(slot)
        if idx is None:
            idx = {}
            kc = [ref.key.cols[i] for i in pat]
            data = self.store.data[ref.key.tab.name]
            for pid, pv in data.items():
                idx.setdefault(tuple(pv[c] for c in kc), []).append(pid)
            self.up[slot] = idx
        return idx.get(tuple(vals[ref.cols[i]] for i in pat), ())

    def downs(self, ref, pvals):
        """Ids of the rows that match, through `ref`, a key row holding `pvals`."""
        idx = self.down.get(ref.name)
        if idx is None:
            idx = {}
            data = self.store.data[ref.tab.name]
            for cid, cv in data.items():
                pat = form(ref, cv)
                if pat:
                    idx.setdefault(pat, {}).setdefault(
                        tuple(cv[ref.cols[i]] for i in pat), []).append(cid)
            self.down[ref.name] = idx
        out = []
        for pat, table in idx.items():
            hit = table.get(tuple(pvals[ref.key.cols[i]] for i in pat))
            if hit:
                out.extend(hit)
        return out


def book(store):
    got = getattr(store, "book", None)
    if got is None:
        got = store.book = Book(store)
    return got


def spoil(store):
    store.book = None
PYEOF

cat > /app/db/drop.py <<'PYEOF'
from db import clear, hold, match


class Effect:
    """What one delete statement does, worked out against the store before it runs. `gone`
    maps every removed row to the round it goes in."""

    def __init__(self):
        self.gone = {}
        self.lost = []
        self.new = {}
        self.fail = None


def plan(store, tab, ids):
    """Removed set, rounds, lost references, clearing and refusal of `delete tab ids`.

    Every (row, reference) pair keeps a count of the key rows it matched before the statement
    that are still standing. The named rows go in round 0. Removals are counted down one round
    at a time: a pair that reaches zero has lost its reference, and a pair on a cascade
    reference removes its row in the next round unless an earlier pair already did. A row
    therefore goes one round after the last row it matched through the first of its cascade
    references to run out, and never before every row it matched through it has gone, which
    is the smallest set closed under the rule: rows that match only one another never reach
    zero, and neither does a row that matches itself."""
    bk = match.book(store)
    eff = Effect()
    gone = eff.gone
    todo = []
    for rid in ids:
        gone[(tab, rid)] = 0
        todo.append((tab, rid))
    left = {}
    tabs = store.tabs
    step = 0
    while todo:
        step += 1
        nxt = []
        for pt, p in todo:
            pv = store.get(pt, p)
            for ref in tabs[pt].used:
                ct = ref.tab.name
                for c in bk.downs(ref, pv):
                    slot = (ct, c, ref)
                    n = left.get(slot)
                    if n is None:
                        n = len(bk.ups(ref, store.get(ct, c)))
                    n -= 1
                    left[slot] = n
                    if n == 0:
                        eff.lost.append(slot)
                        if ref.act == "cascade" and (ct, c) not in gone:
                            gone[(ct, c)] = step
                            nxt.append((ct, c))
        todo = nxt
    eff.new = clear.wipe(store, eff)
    eff.fail = hold.check(store, bk, eff)
    return eff


def delete(store, tab, ids):
    eff = plan(store, tab, ids)
    if eff.fail is not None:
        return ("refused", eff.fail[0], eff.fail[1])
    for t, rid in eff.gone:
        store.drop(t, rid)
    for (t, rid), vals in eff.new.items():
        old = store.get(t, rid)
        for col, val in enumerate(vals):
            if old[col] != val:
                store.put(t, rid, col, val)
    match.spoil(store)
    return ("ok", len(eff.gone), len(eff.new))
PYEOF

cat > /app/db/clear.py <<'PYEOF'
def wipe(store, eff):
    """New values of every row the statement clears.

    A row is cleared when it lost a setnull reference and is not itself removed; the listed
    columns of every such reference go null, and the removed set, already settled on the old
    values, is not revisited. A row counts as cleared even when those columns were null."""
    new = {}
    for t, rid, ref in eff.lost:
        if ref.act != "setnull" or (t, rid) in eff.gone:
            continue
        vals = new.get((t, rid))
        if vals is None:
            vals = new[(t, rid)] = list(store.get(t, rid))
        for col in ref.wipe:
            vals[col] = None
    return new
PYEOF

cat > /app/db/hold.py <<'PYEOF'
from db import match

LIMIT = 15


def check(store, bk, eff):
    """The refusal of a planned delete, as (declaration name, row id), or None.

    A restrict reference fails on any row that lost it, removed or not, and a row removed
    deeper than the limit fails every cascade reference it lost. Everything else is judged on
    the end state: the remaining rows with their values after clearing. Only a row that lost a
    reference, or that matched a key row whose key was cleared, can be in a different position
    from the one it was in before, so only those are checked."""
    bad = []
    look = set()
    for t, rid, ref in eff.lost:
        if ref.act == "restrict":
            bad.append((ref.pos, rid))
        if ref.act == "cascade" and eff.gone.get((t, rid), 0) > LIMIT:
            bad.append((ref.pos, rid))
        if (t, rid) not in eff.gone:
            look.add((t, rid))
    moved = {}
    for (t, rid), vals in eff.new.items():
        old = store.get(t, rid)
        for key in store.tabs[t].keys:
            if any(vals[c] != old[c] for c in key.cols):
                moved[(t, rid)] = vals
                for ref in store.tabs[t].used:
                    if ref.key is key:
                        for c in bk.downs(ref, old):
                            if (ref.tab.name, c) not in eff.gone:
                                look.add((ref.tab.name, c))
    for t, rid in look:
        vals = eff.new.get((t, rid)) or store.get(t, rid)
        tab = store.tabs[t]
        for ref in tab.refs:
            pat = match.form(ref, vals)
            if pat is None:
                continue
            if pat is False or not standing(bk, eff, moved, ref, pat, vals):
                bad.append((ref.pos, rid))
        for key in tab.keys:
            if any(vals[c] is None for c in key.cols):
                bad.append((key.pos, rid))
    if not bad:
        return None
    pos = min(p for p, _ in bad)
    return (store.script.decls[pos].name, min(rid for p, rid in bad if p == pos))


def standing(bk, eff, moved, ref, pat, vals):
    """Whether some key row still matches `vals` once the statement is done."""
    kt = ref.key.tab.name
    for p in bk.ups(ref, vals, pat):
        if (kt, p) in eff.gone:
            continue
        pv = moved.get((kt, p))
        if pv is not None and any(pv[ref.key.cols[i]] is None for i in pat):
            continue
        return True
    return False
PYEOF

cat > /app/db/audit.py <<'PYEOF'
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
            for y in part:
                if y >= n:
                    meets[y - n] = settle(y)
            moved = False
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
PYEOF
