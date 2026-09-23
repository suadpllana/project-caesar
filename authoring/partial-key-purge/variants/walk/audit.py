from db import hold, match


def audit(store):
    """Correct variant: rounds from bounded forward deletes.

    Deleter sets (the rows whose lone delete removes a row) come from components of the
    cascade-match graph found by Kosaraju's two passes, settled dependencies first, loops grown
    from each row alone. The rows a lone delete removes within the depth limit are found the
    direct way, by running the delete forward from every row for at most fifteen rounds with
    per-(row, reference) counters, and inverted into sets. Refusals are painted in declaration
    and id order."""
    bk = match.book(store)
    rows = []
    where = {}
    for t in store.script.tabs:
        for rid in store.ids(t.name):
            where[(t.name, rid)] = len(rows)
            rows.append((t, rid))
    n = len(rows)
    refs = []
    for t, rid in rows:
        vals = store.get(t.name, rid)
        mine = []
        for ref in t.refs:
            pat = match.form(ref, vals)
            if pat:
                mine.append((ref, [where[(ref.key.tab.name, p)] for p in bk.ups(ref, vals, pat)]))
        refs.append(mine)
    cas = [[ms for ref, ms in refs[v] if ref.act == "cascade" and ms] for v in range(n)]

    out_edges = [sorted({u for ms in cas[v] for u in ms}) for v in range(n)]
    in_edges = [[] for _ in range(n)]
    for v in range(n):
        for u in out_edges[v]:
            in_edges[u].append(v)
    done = [False] * n
    finish = []
    for s in range(n):
        if done[s]:
            continue
        done[s] = True
        stack = [(s, 0)]
        while stack:
            v, i = stack[-1]
            if i < len(out_edges[v]):
                stack[-1] = (v, i + 1)
                u = out_edges[v][i]
                if not done[u]:
                    done[u] = True
                    stack.append((u, 0))
            else:
                stack.pop()
                finish.append(v)
    comp = [-1] * n
    groups = []
    for s in reversed(finish):
        if comp[s] >= 0:
            continue
        comp[s] = len(groups)
        members = [s]
        todo = [s]
        while todo:
            v = todo.pop()
            for w in in_edges[v]:
                if comp[w] < 0:
                    comp[w] = comp[s]
                    members.append(w)
                    todo.append(w)
        groups.append(members)

    dels = [0] * n
    cache = {}

    def cut(ms, keep):
        key = tuple(ms)
        if keep:
            got = cache.get(key)
            if got is not None:
                return got
        got = dels[ms[0]]
        for u in ms[1:]:
            got &= dels[u]
            if not got:
                break
        if keep:
            cache[key] = got
        return got

    for members in reversed(groups):
        mine = set(members)
        cyclic = len(members) > 1 or members[0] in out_edges[members[0]]
        if not cyclic:
            v = members[0]
            got = 1 << v
            for ms in cas[v]:
                got |= cut(ms, True)
            dels[v] = got
            continue
        for v in members:
            dels[v] = 1 << v
        change = True
        while change:
            change = False
            for v in members:
                got = 1 << v
                for ms in cas[v]:
                    got |= cut(ms, not mine.intersection(ms))
                if got != dels[v]:
                    dels[v] = got
                    change = True

    limit = hold.LIMIT
    feeds = [[] for _ in range(n)]
    for v in range(n):
        for i, ms in enumerate(cas[v]):
            for u in ms:
                feeds[u].append((v, i, len(ms)))
    quick = [[] for _ in range(n)]
    for r in range(n):
        taken = {r}
        tally = {}
        front = [r]
        depth = 0
        while front and depth < limit:
            depth += 1
            nxt = []
            for u in front:
                for v, i, size in feeds[u]:
                    k = tally.get((v, i), 0) + 1
                    tally[(v, i)] = k
                    if k == size and v not in taken:
                        taken.add(v)
                        nxt.append(v)
            front = nxt
        for v in taken:
            quick[v].append(r)
    early = []
    width = (n + 7) // 8
    for v in range(n):
        buf = bytearray(width)
        for r in quick[v]:
            buf[r >> 3] |= 1 << (r & 7)
        early.append(int.from_bytes(buf, "little"))

    total = count_columns(dels, n)
    lost_sets = []
    for v in range(n):
        acc = 0
        for ref, ms in refs[v]:
            if ref.act == "setnull" and ms:
                acc |= cut(ms, True)
        acc &= ~dels[v]
        if acc:
            lost_sets.append(acc)
    wiped = count_columns(lost_sets, n)

    def standing(v):
        t, rid = rows[v]
        vals = store.get(t.name, rid)
        sn = [(ref, cut(ms, True) if ms else 0) for ref, ms in refs[v] if ref.act == "setnull"]
        cases = []
        for mask in range(1 << len(sn)):
            region = ~dels[v]
            now = list(vals)
            for i, (ref, lost) in enumerate(sn):
                if mask >> i & 1:
                    region &= lost
                    for c in ref.wipe:
                        now[c] = None
                else:
                    region &= ~lost
            if region:
                cases.append((region, now))
        return cases

    free = (1 << n) - 1
    name = [None] * n
    for decl in store.script.decls:
        if not free:
            break
        t = decl.tab
        for rid in store.ids(t.name):
            v = where[(t.name, rid)]
            hit = 0
            if hasattr(decl, "act"):
                for ref, ms in refs[v]:
                    if ref is decl and ms:
                        if ref.act == "restrict":
                            hit |= cut(ms, True)
                        elif ref.act == "cascade":
                            hit |= cut(ms, True) & ~early[v]
                for region, now in standing(v):
                    pat = match.form(decl, now)
                    if pat is None:
                        continue
                    if pat is False:
                        hit |= region
                        continue
                    ms = [where[(decl.key.tab.name, p)] for p in bk.ups(decl, now, pat)]
                    hit |= (region & cut(ms, True)) if ms else region
            else:
                for region, now in standing(v):
                    if any(now[c] is None for c in decl.cols):
                        hit |= region
            hit &= free
            if hit:
                free ^= hit
                while hit:
                    top = hit.bit_length() - 1
                    name[top] = (decl.name, rid)
                    hit ^= 1 << top
    return [(t.name, rid, total[v], wiped[v], name[v]) for v, (t, rid) in enumerate(rows)]


def count_columns(sets, n):
    digits = []
    for bits in sets:
        i = 0
        while bits:
            if i == len(digits):
                digits.append(bits)
                break
            d = digits[i]
            digits[i] = d ^ bits
            bits &= d
            i += 1
    out = [0] * n
    for i, d in enumerate(digits):
        text = format(d, "b")[::-1]
        for v in range(min(n, len(text))):
            if text[v] == "1":
                out[v] += 1 << i
    return out
