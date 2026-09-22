"""Wrong readings as whole solvers, v2, for measuring what each one moves (scratch)."""
from core import RIGHT, Rules, initial
import settle
from settle import det, expand_gap, gap_caps, rank


def backward(trace, live_after_end):
    live_after = live_after_end
    gl = {}
    for k in range(len(trace) - 1, -1, -1):
        t = trace[k]
        if t[0] == "det":
            live_after = {x for x, y in t[1].items() if y in live_after}
            continue
        _t, starts, edges, exits = t
        live = set()
        for u in sorted(edges, key=rank, reverse=True):
            if (u in exits and u[0] in live_after) or any(v in live for _l, v in edges[u]):
                live.add(u)
        gl[k] = (live, live_after)
        live_after = {x for x in starts if (x, 0) in live}
    return gl


def emit(out, n, restored, cand):
    out.append("gap %d" % n)
    out.extend(restored)
    if cand is not None:
        out.append("? " + " | ".join(cand))


def local(cfg, items, rules=RIGHT):
    """Each span settled with evidence only up to the start of the next span."""
    trace, _gl = settle.settle(cfg, items, rules)
    gaps = [k for k, t in enumerate(trace) if t[0] == "gap"]
    out = []
    for n, k in enumerate(gaps):
        _t, starts, edges, exits = trace[k]
        stop = gaps[n + 1] if n + 1 < len(gaps) else len(items)
        la = set()
        for u in exits:
            x = u[0]
            for i in range(k + 1, stop):
                x = det(x, items[i], cfg, rules)
                if x is None:
                    break
            if x is not None:
                la.add(u[0])
        live = set()
        for u in sorted(edges, key=rank, reverse=True):
            if (u in exits and u[0] in la) or any(v in live for _l, v in edges[u]):
                live.add(u)
        restored, cand = settle.walk(trace, {k: (live, la)}, k)
        emit(out, n + 1, restored, cand)
    return out


def single(cfg, items, rules=RIGHT):
    """Global liveness, but each span starts from the one table that the lexicographically
    first live filling of the span before it leaves."""
    L = cfg[0]
    node = (initial(L), 0, 0, 0, 0, None)
    out = []
    n = 0
    i = 0
    while i < len(items):
        it = items[i]
        if it[0] != "gap":
            node = det(node, it, cfg, rules)
            if node is None:
                return out + ["<dead>"]
            i += 1
            continue
        n += 1
        trace, gl = settle.settle(cfg, items[i:], rules, start=node)
        restored, cand = settle.walk(trace, gl, 0)
        emit(out, n, restored, cand)
        _t, starts, edges, exits = trace[0]
        live, la = gl[0]
        u = (node, 0)
        while not (u in exits and u[0] in la):
            u = min((lab or "", v) for lab, v in edges[u] if v in live)[1]
        node = u[0]
        i += 1
    return out


def shortest(cfg, items, rules=RIGHT):
    """The shipped plan: span by span, from one table, the shortest fillings that keep the
    journal consistent up to the next span; doubt only among fillings of that length."""
    L = cfg[0]
    caps = gap_caps(items, rules)
    node = (initial(L), 0, 0, 0, 0, None)
    out = []
    n = 0
    gaps = [k for k, it in enumerate(items) if it[0] == "gap"]
    i = 0
    while i < len(items):
        it = items[i]
        if it[0] != "gap":
            node = det(node, it, cfg, rules)
            if node is None:
                return out + ["<dead>"]
            i += 1
            continue
        n += 1
        stop = next((g for g in gaps if g > i), len(items))
        edges, exits = expand_gap({node}, it[1], cfg, caps[i], rules, {})
        good = set()
        for u in exits:
            x = u[0]
            for jj in range(i + 1, stop):
                x = det(x, items[jj], cfg, rules)
                if x is None:
                    break
            if x is not None:
                good.add(u)
        level = {(node, 0): [()]}
        fills = []
        while level and not fills:
            nxt = {}
            for u, paths in level.items():
                if u in good:
                    fills.extend((p, u) for p in paths)
            if fills:
                break
            for u, paths in level.items():
                for lab, v in edges.get(u, []):
                    ext = [p + ((lab,) if lab else ()) for p in paths]
                    if lab is None:
                        level.setdefault(v, [])
                    nxt.setdefault(v, []).extend(ext)
            level = nxt
        if not fills:
            return out + ["<dead>"]
        seqs = sorted(set(p for p, _u in fills))
        pre = []
        dd = 0
        while True:
            nx = {s[dd] if dd < len(s) else "-" for s in seqs}
            if len(nx) == 1 and "-" not in nx:
                pre.append(next(iter(nx)))
                dd += 1
                continue
            emit(out, n, pre, None if nx == {"-"} else sorted(nx))
            break
        node = min(fills)[1][0]
        i += 1
    return out


def safe(fn):
    def run(cfg, items):
        try:
            return fn(cfg, items)
        except Exception as exc:  # a wrong reading may find the journal impossible
            return ["<error %s>" % type(exc).__name__]
    return run


READINGS = {
    "shortest": safe(shortest),
    "local": safe(local),
    "single": safe(single),
    "forward-only": safe(lambda c, it: settle.restore(c, it, opts={"backward": False})),
    "merge-fp": safe(lambda c, it: settle.restore(c, it, opts={"merge_fp": True})),
    "float-dig": safe(lambda c, it: settle.restore(c, it, opts={"float_dig": True})),
    "audit-at-end": safe(lambda c, it: settle.restore(c, it, opts={"audit_end": True})),
    "no-end": safe(lambda c, it: settle.restore(c, it, opts={"no_end": True})),
    "pass-uncounted": safe(lambda c, it: settle.restore(c, it, Rules(pass_counts=False))),
    "waiting-sends": safe(lambda c, it: settle.restore(c, it, Rules(silence=False))),
    "beat-anytime": safe(lambda c, it: settle.restore(c, it, Rules(beat_hold=False))),
    "no-depth": safe(lambda c, it: settle.restore(c, it, Rules(depth=False))),
}
