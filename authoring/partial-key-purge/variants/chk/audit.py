from db import hold, match


def audit(store):
    """Correct variant: deleter sets by a worklist, rounds by capped round maps.

    For every row, the set of rows whose lone delete removes it (a bit set in an int) is grown
    from the row alone by a worklist over the whole store, no components: a row is re-evaluated
    whenever a row it matched through a cascade reference grows, starting from an order in
    which what a row depends on comes first. For the depth limit each row keeps a small map
    from deleter to the round it is removed in, capped at the limit: a match set's map holds
    the deleters common to all its rows with the latest of their rounds plus one, and a row
    takes, per deleter, the earliest round over its cascade references. Failures are listed as
    (declaration, id, deleters), sorted, and the first to reach a deleter names its refusal."""
    idx = match.ix(store)
    rows = [(t.name, rid) for t in store.script.tabs for rid in store.ids(t.name)]
    num = {r: i for i, r in enumerate(rows)}
    n = len(rows)
    refs_of = {t.name: t.refs for t in store.script.tabs}
    live = []
    for t, rid in rows:
        vals = store.get(t, rid)
        got = []
        for ref in refs_of[t]:
            pat = match.shape(ref, vals)
            if pat:
                got.append((ref, tuple(num[(ref.key.tab.name, p)]
                                       for p in idx.parents(ref, pat, vals))))
        live.append(got)
    need = [[ms for ref, ms in live[v] if ref.act == "cascade" and ms] for v in range(n)]
    watchers = [[] for _ in range(n)]
    for v in range(n):
        for ms in need[v]:
            for u in ms:
                watchers[u].append(v)

    deps_of = [[u for ms in need[v] for u in ms] for v in range(n)]
    order = []
    seen = [False] * n
    for s in range(n):
        if seen[s]:
            continue
        seen[s] = True
        stack = [(s, 0)]
        while stack:
            v, i = stack[-1]
            deps = deps_of[v]
            if i < len(deps):
                stack[-1] = (v, i + 1)
                u = deps[i]
                if not seen[u]:
                    seen[u] = True
                    stack.append((u, 0))
            else:
                stack.pop()
                order.append(v)

    kills = [1 << v for v in range(n)]

    def both(ms):
        acc = kills[ms[0]]
        for u in ms[1:]:
            acc &= kills[u]
            if not acc:
                break
        return acc

    for v in order:
        got = 1 << v
        for ms in need[v]:
            got |= both(ms)
        kills[v] = got
    queued = [True] * n
    work = list(reversed(order))
    while work:
        v = work.pop()
        queued[v] = False
        got = 1 << v
        for ms in need[v]:
            got |= both(ms)
        if got != kills[v]:
            kills[v] = got
            for w in watchers[v]:
                if not queued[w]:
                    queued[w] = True
                    work.append(w)

    cap = hold.DEEPEST
    rounds = [{v: 0} for v in range(n)]
    for _ in range(cap):
        nxt = []
        for v in range(n):
            if not need[v]:
                nxt.append(rounds[v])
                continue
            mine = {v: 0}
            for ms in need[v]:
                common = dict(rounds[ms[0]])
                for u in ms[1:]:
                    other = rounds[u]
                    common = {r: max(k, other[r]) for r, k in common.items() if r in other}
                    if not common:
                        break
                for r, k in common.items():
                    if k < cap and mine.get(r, cap + 1) > k + 1:
                        mine[r] = k + 1
            nxt.append(mine)
        rounds = nxt
    soon = []
    size = (n + 7) // 8
    for v in range(n):
        raw = bytearray(size)
        for r in rounds[v]:
            raw[r >> 3] |= 1 << (r & 7)
        soon.append(int.from_bytes(raw, "little"))

    removed = columns(kills, n)
    blanks = []
    for v in range(n):
        lost = 0
        for ref, ms in live[v]:
            if ref.act == "setnull" and ms:
                lost |= both(ms)
        lost &= ~kills[v]
        if lost:
            blanks.append(lost)
    cleared = columns(blanks, n)

    items = []
    decls = store.script.decls
    for d, decl in enumerate(decls):
        for rid in store.ids(decl.tab.name):
            items.append((d, rid, num[(decl.tab.name, rid)]))

    def after(v):
        t, rid = rows[v]
        vals = store.get(t, rid)
        nulls = [(ref, both(ms) if ms else 0) for ref, ms in live[v] if ref.act == "setnull"]
        for mask in range(1 << len(nulls)):
            left = ~kills[v]
            now = list(vals)
            for i, (ref, lost) in enumerate(nulls):
                if mask >> i & 1:
                    left &= lost
                    for c in ref.wipe:
                        now[c] = None
                else:
                    left &= ~lost
            if left:
                yield left, now

    def failing(decl, v):
        acc = 0
        if hasattr(decl, "act"):
            for ref, ms in live[v]:
                if ref is decl and ms:
                    if decl.act == "restrict":
                        acc |= both(ms)
                    elif decl.act == "cascade":
                        acc |= both(ms) & ~soon[v]
            for left, now in after(v):
                pat = match.shape(decl, now)
                if pat is None:
                    continue
                if pat is False:
                    acc |= left
                    continue
                ms = tuple(num[(decl.key.tab.name, p)] for p in idx.parents(decl, pat, now))
                acc |= (left & both(ms)) if ms else left
        else:
            for left, now in after(v):
                if any(now[c] is None for c in decl.cols):
                    acc |= left
        return acc

    free = (1 << n) - 1
    said = [None] * n
    for d, rid, v in sorted(items):
        if not free:
            break
        hit = failing(decls[d], v) & free
        if hit:
            free &= ~hit
            while hit:
                low = hit & -hit
                said[low.bit_length() - 1] = (decls[d].name, rid)
                hit ^= low
    return [(t, rid, removed[v], cleared[v], said[v]) for v, (t, rid) in enumerate(rows)]


def columns(sets, n):
    levels = []
    for x in sets:
        k = 0
        while x:
            if k == len(levels):
                levels.append(x)
                break
            y = levels[k]
            levels[k] = y ^ x
            x &= y
            k += 1
    out = [0] * n
    for k, lv in enumerate(levels):
        s = bin(lv)[2:][::-1]
        for v in range(min(n, len(s))):
            if s[v] == "1":
                out[v] += 1 << k
    return out
