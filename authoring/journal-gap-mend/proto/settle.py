"""Prototype reference, v2: settle the whole journal forward, prune backward, walk spans.

A node is (table, g, a, r, b, pend): the full table with depths and queues, the running
totals, and the digest the last surviving entry obliges the very next line to be.

Inside a lost span the markers (digests and audits, in the order written) are consumed in
order: a digest exactly when the entry that triggers it is taken, an audit at any point
between entries where the totals and the full-table fingerprint match.

opts (wrong readings only; the reference uses none):
  backward=False   candidates from forward-reachable nodes only
  merge_fp=True    nodes keyed by holder fingerprint instead of the full table
  float_dig=True   an in-span digest may be matched at any point between entries
  audit_end=True   an in-span audit is checked against the table the span ends with
  no_end=True      the end of a span is never offered as a candidate
"""
from core import RIGHT, apply, ffp, fp, initial, label, requests


def contrib(entry, rules):
    """What a surviving entry adds to (g, a, r, b), read off its recorded outcome."""
    if entry[0] == "beat":
        return (0, 0, 0, 1)
    if entry[0] == "acq":
        return (1 if entry[3] == "grant" else 0, 1, 0, 0)
    return (1 if entry[3] == "pass" and rules.pass_counts else 0, 0, 1, 0)


def gap_caps(items, rules=RIGHT):
    """Caps on (g, a, r, b) when each span is left: every later audit's totals, and every
    later digest's grant total, less what the surviving entries before it add. Scanning stops
    at the first surviving audit."""
    caps = {}
    INF = 10 ** 9
    for i, it in enumerate(items):
        if it[0] != "gap":
            continue
        acc = [0, 0, 0, 0]
        cap = [INF, INF, INF, INF]

        def audit(t):
            for k in range(4):
                cap[k] = min(cap[k], t[1 + k] - acc[k])

        for j in range(i + 1, len(items)):
            t = items[j]
            if t[0] == "e":
                for k, v in enumerate(contrib(t[1], rules)):
                    acc[k] += v
            elif t[0] == "d":
                cap[0] = min(cap[0], t[1] - acc[0])
            elif t[0] == "s":
                audit(t)
                break
            else:
                for m in t[1]:
                    if m[0] == "d":
                        cap[0] = min(cap[0], m[1] - acc[0])
                    else:
                        audit(m)
        caps[i] = tuple(cap)
    return caps


def key(node, opts):
    if opts.get("merge_fp"):
        st, g, a, r, b, p = node
        return (fp(st), g, a, r, b, p)
    return node


def step_entry(node, entry, cfg, rules):
    """A surviving entry: legal, same outcome, and the digest obligation it creates."""
    st, g, a, r, b, pend = node
    if pend is not None:
        return None
    req = entry[:3] if entry[0] != "beat" else entry[:2]
    res = apply(st, req, rules)
    if res is None or res[0] != entry:
        return None
    _e, st2, dg, da, dr, db = res
    g2 = g + dg
    p2 = (g2, fp(st2)) if dg and g2 % cfg[2] == 0 else None
    return (st2, g2, a + da, r + dr, b + db, p2)


def det(node, it, cfg, rules):
    st, g, a, r, b, pend = node
    if it[0] == "e":
        return step_entry(node, it[1], cfg, rules)
    if it[0] == "d":
        return (st, g, a, r, b, None) if pend == (it[1], it[2]) else None
    return node if pend is None and (g, a, r, b, ffp(st)) == it[1:] else None


def audit_ok(node, m):
    st, g, a, r, b, _p = node
    return (g, a, r, b, ffp(st)) == m[1:]


def expand_gap(starts, marks, cfg, cap, rules, opts):
    """Every filling of one span from each start node.

    Returns (edges, exits): edges maps an inner node (node, j) to [(label, inner')], where a
    label of None consumes an audit; exits are inner nodes that may leave the span."""
    L, S, K = cfg
    G, A, R, B = cap
    if opts.get("audit_end"):
        audits = [m for m in marks if m[0] == "s"]
        marks = [m for m in marks if m[0] == "d"]
    m = len(marks)
    edges = {}
    frontier = [(x, 0) for x in starts]
    seen = set(frontier)
    exits = set()
    while frontier:
        nxt = []
        for inner in frontier:
            node, j = inner
            st, g, a, r, b, _p = node
            out = []
            if j < m and marks[j][0] == "s" and audit_ok(node, marks[j]):
                out.append((None, (node, j + 1)))
            if (j < m and marks[j][0] == "d" and opts.get("float_dig")
                    and marks[j][1:] == (g, fp(st))):
                out.append((None, (node, j + 1)))
            if j == m and (not opts.get("audit_end") or all(audit_ok(node, x) for x in audits)):
                exits.add(inner)
            for req in requests(st, L, S):
                res = apply(st, req, rules)
                if res is None:
                    continue
                entry, st2, dg, da, dr, db = res
                g2, a2, r2, b2 = g + dg, a + da, r + dr, b + db
                if g2 > G or a2 > A or r2 > R or b2 > B:
                    continue
                j2 = j
                if dg and g2 % K == 0 and not opts.get("float_dig"):
                    if j2 < m and marks[j2] == ("d", g2, fp(st2)):
                        j2 += 1
                    else:
                        continue
                out.append((label(entry), ((st2, g2, a2, r2, b2, None), j2)))
            edges[inner] = out
            for _lab, tgt in out:
                if tgt not in seen:
                    seen.add(tgt)
                    nxt.append(tgt)
        frontier = nxt
    return edges, exits


def rank(inner):
    node, j = inner
    return node[2] + node[3] + node[4], j


def settle(cfg, items, rules=RIGHT, opts=None, start=None):
    opts = opts or {}
    L, S, K = cfg
    caps = gap_caps(items, rules)
    layer = {start or (initial(L), 0, 0, 0, 0, None)}
    trace = []
    for i, it in enumerate(items):
        if it[0] == "gap":
            starts = {x for x in layer if x[5] is None}
            edges, exits = expand_gap(starts, it[1], cfg, caps[i], rules, opts)
            trace.append(("gap", starts, edges, exits))
            layer = {inner[0] for inner in exits}
        else:
            mp = {}
            for x in layer:
                y = det(x, it, cfg, rules)
                if y is not None:
                    mp[x] = y
            trace.append(("det", mp))
            layer = set(mp.values())
        if opts.get("merge_fp"):
            kept = {}
            for x in sorted(layer, key=repr):
                kept.setdefault(key(x, opts), x)
            layer = set(kept.values())
    live_after = layer
    gap_live = {}
    for k in range(len(trace) - 1, -1, -1):
        t = trace[k]
        if t[0] == "det":
            live_after = {x for x, y in t[1].items() if y in live_after}
            continue
        _tag, starts, edges, exits = t
        la = {u[0] for u in exits} if opts.get("backward") is False else live_after
        live = set()
        for u in sorted(edges, key=rank, reverse=True):
            if (u in exits and u[0] in la) or any(v in live for _l, v in edges[u]):
                live.add(u)
        gap_live[k] = (live, la)
        live_after = {x for x in starts if (x, 0) in live}
    return trace, gap_live


def closure(cur, edges, live):
    out = set(cur)
    stack = list(cur)
    while stack:
        u = stack.pop()
        for lab, v in edges[u]:
            if lab is None and v in live and v not in out:
                out.add(v)
                stack.append(v)
    return out


def walk(trace, gap_live, k, opts=None):
    opts = opts or {}
    _tag, starts, edges, exits = trace[k]
    live, la = gap_live[k]
    cur = {(x, 0) for x in starts if (x, 0) in live}
    restored = []
    while True:
        cur = closure(cur, edges, live)
        cand = set()
        for u in cur:
            if u in exits and u[0] in la and not opts.get("no_end"):
                cand.add("-")
            for lab, v in edges[u]:
                if lab is not None and v in live:
                    cand.add(lab)
        if len(cand) == 1 and "-" not in cand:
            lab = next(iter(cand))
            restored.append(lab)
            cur = {v for u in cur for l2, v in edges[u] if l2 == lab and v in live}
            continue
        if cand == {"-"} or not cand:
            return restored, None
        return restored, sorted(cand)


def restore(cfg, items, rules=RIGHT, opts=None):
    opts = opts or {}
    trace, gap_live = settle(cfg, items, rules, opts)
    out = []
    n = 0
    for k, t in enumerate(trace):
        if t[0] != "gap":
            continue
        n += 1
        restored, cand = walk(trace, gap_live, k, opts)
        out.append("gap %d" % n)
        out.extend(restored)
        if cand is not None:
            out.append("? " + " | ".join(cand))
    return out
