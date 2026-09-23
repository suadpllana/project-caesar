"""Sealed model of the row store. Root-only at grading time; never importable by agent code.

Written apart from the reference in `solution/`, and checked against a brute-force transcription
of the contract on generated stores before anything was frozen. It reads scripts itself rather
than through the shipped reader, so a change to the shipped tree cannot move it.

Deletes: removal runs in rounds, breadth first. The named rows are round 0; every (row,
reference) pair keeps a count of the rows it matched that are still standing, and a pair on a
cascade reference that reaches zero while its row is standing removes that row in the next
round. Processing a whole round before the next one makes a row's round one more than the round
of the last row it matched through the first of its cascade references to run out. That is the
smallest removed set closed under the rule, because nothing is removed before every row it
matched through that reference has been. Matching reads the values from before the statement.
A restrict reference fails on any row that lost it; a row removed after round fifteen fails
every cascade reference it lost; everything else is read off the end state.

Audit: for every row v the model builds dels[v], the set of rows whose lone delete removes v,
as a Python integer with one bit per row. A row goes when all rows it matched through one of
its cascade references go, so dels[v] is v itself plus, over its cascade references, the
intersection of dels over each reference's matches. Rows are grouped into strongly connected
components of the "matched through a cascade reference" graph (Kosaraju), settled with every
component they depend on first; inside a loop the sets are grown from the row alone until they
stop changing, which is the smallest solution and so keeps rows that only match one another.
Rounds come from a second, forward computation: a bounded breadth-first delete from every row,
fifteen rounds deep, inverted into the set of rows that remove v within the limit. Counts are
column sums over the sets. Every failure a lone delete can cause is written as (declaration
position, row id, set of deleters); sorted, they are painted onto the deleters, and each
deleter keeps the first one that reaches it, which is the refusal it prints.
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


LIMIT = 15


def attempt(db, ix, tab, ids):
    """(removed, cleared, new values, failure) of `delete tab ids` over ix.data; nothing is
    changed. `removed` maps every removed row to the round it goes in."""
    data = ix.data
    gone = {}
    wave = []
    for i in ids:
        gone[(tab, i)] = 0
        wave.append((tab, i))
    left = {}
    lost = []
    depth = 0
    while wave:
        depth += 1
        nxt = []
        for pt, p in wave:
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
                            gone[(ct, c)] = depth
                            nxt.append((ct, c))
        wave = nxt
    fails = []
    new = {}
    wiped = set()
    look = set()
    for ct, c, rn in lost:
        r = db.refs[rn]
        if r["act"] == "restrict":
            fails.append((r["pos"], c))
        if r["act"] == "cascade" and gone.get((ct, c), 0) > LIMIT:
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


def components(n, deps):
    """Strongly connected components of the graph v -> deps[v], each a list, ordered so that
    every component comes after all components it has an edge into (Kosaraju)."""
    back = [[] for _ in range(n)]
    for v in range(n):
        for u in deps[v]:
            back[u].append(v)
    seen = [False] * n
    order = []
    for s in range(n):
        if seen[s]:
            continue
        seen[s] = True
        stack = [(s, iter(deps[s]))]
        while stack:
            v, it = stack[-1]
            for u in it:
                if not seen[u]:
                    seen[u] = True
                    stack.append((u, iter(deps[u])))
                    break
            else:
                stack.pop()
                order.append(v)
    comp = [-1] * n
    comps = []
    for s in reversed(order):
        if comp[s] != -1:
            continue
        comp[s] = len(comps)
        part = [s]
        todo = [s]
        while todo:
            v = todo.pop()
            for u in back[v]:
                if comp[u] == -1:
                    comp[u] = comp[s]
                    part.append(u)
                    todo.append(u)
        comps.append(part)
    comps.reverse()
    return comps


def columns(sets, n):
    """For each bit position below n, how many of `sets` have it: vertical binary counters,
    one integer per binary digit of the count."""
    planes = []
    for x in sets:
        carry = x
        k = 0
        while carry:
            if k == len(planes):
                planes.append(0)
            both = planes[k] & carry
            planes[k] ^= carry
            carry = both
            k += 1
    out = [0] * n
    for k, plane in enumerate(planes):
        bits = format(plane, "b")[::-1]
        for v, ch in enumerate(bits[:n]):
            if ch == "1":
                out[v] += 1 << k
    return out


def audit(db, ix):
    """(table, id, removed, cleared, refusal or None) of a lone delete of every row."""
    data = ix.data
    rows = [(t, rid) for t in db.order for rid in sorted(data[t])]
    pos = {row: i for i, row in enumerate(rows)}
    n = len(rows)
    bit = [1 << v for v in range(n)]
    live = []
    for t, rid in rows:
        vals = data[t][rid]
        mine = []
        for r in db.out_refs[t]:
            pat = shape(r, vals)
            if pat:
                mine.append((r, pat, tuple(pos[(r["ktab"], p)] for p in ix.parents(r, pat, vals))))
        live.append(mine)
    sup = [[ms for r, _, ms in live[v] if r["act"] == "cascade" and ms] for v in range(n)]
    deps = [sorted({u for ms in sup[v] for u in ms}) for v in range(n)]

    dels = [0] * n
    final = set()
    meet_memo = {}

    def meet(ms, cache=True):
        if not ms:
            return 0
        got = meet_memo.get(ms) if cache else None
        if got is None:
            got = dels[ms[0]]
            for u in ms[1:]:
                got &= dels[u]
                if not got:
                    break
            if cache:
                meet_memo[ms] = got
        return got

    for part in components(n, deps):
        inside = set(part)
        loop = len(part) > 1 or part[0] in deps[part[0]]
        if not loop:
            v = part[0]
            got = bit[v]
            for ms in sup[v]:
                got |= meet(ms)
            dels[v] = got
            continue
        for v in part:
            dels[v] = bit[v]
        grew = True
        while grew:
            grew = False
            for v in part:
                got = bit[v]
                for ms in sup[v]:
                    got |= meet(ms, cache=not inside.intersection(ms))
                if got != dels[v]:
                    dels[v] = got
                    grew = True

    # rows whose lone delete removes each row within LIMIT rounds, from bounded forward deletes
    users = [[] for _ in range(n)]
    for v in range(n):
        for s, ms in enumerate(sup[v]):
            for u in ms:
                users[u].append((v, s))
    within = [[] for _ in range(n)]
    for r in range(n):
        when = {r: 0}
        count = {}
        wave = [r]
        for k in range(1, LIMIT + 1):
            nxt = []
            for u in wave:
                for v, s in users[u]:
                    c = count.get((v, s), 0) + 1
                    count[(v, s)] = c
                    if c == len(sup[v][s]) and v not in when:
                        when[v] = k
                        nxt.append(v)
            if not nxt:
                break
            wave = nxt
        for v in when:
            within[v].append(r)
    width = (n + 7) // 8
    soon = []
    for v in range(n):
        buf = bytearray(width)
        for r in within[v]:
            buf[r >> 3] |= 1 << (r & 7)
        soon.append(int.from_bytes(bytes(buf), "little"))

    removed = columns(dels, n)
    wipes = []
    for v in range(n):
        lost = 0
        for r, _, ms in live[v]:
            if r["act"] == "setnull":
                lost |= meet(ms)
        lost &= ~dels[v]
        if lost:
            wipes.append(lost)
    cleared = columns(wipes, n)

    def situations(v):
        """(deleters, values) for every way row v can stand at the end: it is not removed and
        exactly the setnull references in some subset have lost, possibly none."""
        t, rid = rows[v]
        vals = data[t][rid]
        nulls = [(r, meet(ms)) for r, _, ms in live[v] if r["act"] == "setnull"]
        out = []
        for mask in range(1 << len(nulls)):
            where = ~dels[v]
            now = list(vals)
            for i, (r, lost) in enumerate(nulls):
                if mask >> i & 1:
                    where &= lost
                    for c in r["wipe"]:
                        now[c] = None
                else:
                    where &= ~lost
            if where:
                out.append((where, now))
        return out

    def failing(v, decl):
        t, rid = rows[v]
        got = 0
        if decl in db.refs:
            r = db.refs[decl]
            for rr, _, ms in live[v]:
                if rr is r:
                    if r["act"] == "restrict":
                        got |= meet(ms)
                    elif r["act"] == "cascade":
                        got |= meet(ms) & ~soon[v]
            for where, now in situations(v):
                pat = shape(r, now)
                if pat is None:
                    continue
                if pat is False:
                    got |= where
                    continue
                ms = tuple(pos[(r["ktab"], p)] for p in ix.parents(r, pat, now))
                got |= where & meet(ms) if ms else where
        else:
            cols = db.keys[decl][1]
            for where, now in situations(v):
                if any(now[i] is None for i in cols):
                    got |= where
        return got

    todo = []
    for d, decl in enumerate(db.decls):
        t = db.refs[decl]["tab"] if decl in db.refs else db.keys[decl][0]
        for rid in sorted(data[t]):
            todo.append((d, rid, pos[(t, rid)], decl))
    todo.sort()
    open_ = (1 << n) - 1
    refusal = [None] * n
    for d, rid, v, decl in todo:
        if not open_:
            break
        hit = failing(v, decl) & open_
        if not hit:
            continue
        open_ &= ~hit
        while hit:
            r = hit.bit_length() - 1
            refusal[r] = (decl, rid)
            hit ^= 1 << r
    return [(t, rid, removed[v], cleared[v], refusal[v]) for v, (t, rid) in enumerate(rows)]


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
            for t, rid, gone, wiped, fail in audit(db, ix):
                end = "ok" if fail is None else "refused %s %d" % fail
                out.append("%s %d %d %d %s" % (t, rid, gone, wiped, end))
    return out


if __name__ == "__main__":
    import sys
    sys.stdout.write("".join(line + "\n" for line in expect(open(sys.argv[1]).read())))
