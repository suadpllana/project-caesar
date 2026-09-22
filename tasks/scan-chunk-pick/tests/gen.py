"""Segment files generated inside the verifier, from a seed drawn after the agent is gone.

Twelve families, each shaped at one part of the mechanism rather than drawn at random: inexact
headers that only the widening rule survives, dictionaries with and without an overflow list,
chunk partitions that disagree between columns, conditions that collapse the survivor counts
early so every later estimate moves, estimates built to tie, reports over columns a condition
already read, and the two scale shapes the execution limit is set against.

`programs(seed, per)` returns (family, name, lines) with `per` files of every small family and
three of each large one. The same call is made by the worker, which runs them, and by the
grader, which grades them against the sealed model, so both see the same population.
"""
import hashlib
import random

KINDS = ("ge", "le", "eq", "ne", "nn", "nu")

# (name, files) - the two scale families ship three files each whatever `per` is.
FAMILIES = (
    ("plain", False),
    ("widen", False),
    ("dicts", False),
    ("nulls", False),
    ("skew", False),
    ("tight", False),
    ("ties", False),
    ("reuse", False),
    ("empty", False),
    ("multi", False),
    ("wide", True),
    ("deep", True),
)

BIG = 3


def _rng(seed, fam, i):
    h = hashlib.sha256(("%s|%s|%d" % (seed, fam, i)).encode("utf-8")).hexdigest()
    return random.Random(int(h[:16], 16))


def _parts(rng, n, lo, hi):
    """Cut n rows into chunks of between lo and hi rows."""
    out = []
    left = n
    while left > 0:
        take = min(left, rng.randint(lo, hi))
        if left - take < lo and left - take > 0:
            take = left
        out.append(take)
        left -= take
    return out


def _column(rng, sizes, base, span, nullrate, dictrate, litrate, exactrate, g):
    """Values and chunk headers for one column."""
    chunks = []
    for n in sizes:
        vals = []
        for _ in range(n):
            if rng.random() < nullrate:
                vals.append(None)
            else:
                vals.append(base + rng.randrange(span))
        live = [v for v in vals if v is not None]
        nulls = n - len(live)
        if live:
            mn, mx = min(live), max(live)
            exact = rng.random() < exactrate
            if not exact:
                lo = ((mn + g - 1) // g) * g
                hi = (mx // g) * g
                if lo <= hi:
                    mn, mx = lo, hi
                else:
                    exact = True
        else:
            mn = mx = None
            exact = True
        seen = sorted(set(live))
        lit = set()
        if seen and len(seen) <= 12 and rng.random() < dictrate:
            enc = "d"
            if len(seen) > 1 and rng.random() < litrate:
                for v in rng.sample(seen, rng.randint(1, min(2, len(seen) - 1))):
                    lit.add(v)
        else:
            enc = "p"
        chunks.append({"n": n, "vals": vals, "nulls": nulls, "mn": mn, "mx": mx,
                       "exact": exact, "enc": enc, "dic": [v for v in seen if v not in lit],
                       "lit": lit})
    return chunks


def _chunk_line(c, ch):
    head = ["ch", str(c), str(ch["n"]), str(ch["nulls"]),
            "-" if ch["mn"] is None else str(ch["mn"]),
            "-" if ch["mx"] is None else str(ch["mx"]),
            "e" if ch["exact"] else "w", ch["enc"]]
    if ch["enc"] == "p":
        body = ["-" if v is None else str(v) for v in ch["vals"]]
    else:
        dic = ch["dic"]
        at = {v: i for i, v in enumerate(dic)}
        head.append(str(len(dic)))
        head.extend(str(v) for v in dic)
        body = []
        for v in ch["vals"]:
            if v is None:
                body.append("-")
            elif v in at:
                body.append(str(at[v]))
            else:
                body.append("*%d" % v)
    return " ".join(head + body)


def _stats(layout, c):
    vs = []
    for ch in layout[c]:
        for v in ch["vals"]:
            if v is not None:
                vs.append(v)
    vs.sort()
    cnt = {}
    for v in vs:
        cnt[v] = cnt.get(v, 0) + 1
    return vs, cnt


def _build(rng, g, n, layout, cols, queries):
    lines = ["seg %d %d %d" % (g, n, len(layout))]
    for c, chunks in enumerate(layout):
        for ch in chunks:
            lines.append(_chunk_line(c, ch))
    lines.extend(queries)
    return lines


def _queries(rng, layout, nq, nc, kinds, nproj, pool=None):
    k = len(layout)
    stats = {c: _stats(layout, c) for c in range(k)}

    def one(c, kind):
        vs, cnt = stats[c]
        if kind in ("nn", "nu"):
            return "prd %s %d" % (kind, c)
        if not vs:
            return "prd %s %d 0" % (kind, c)
        last = len(vs) - 1
        if kind == "ge":
            v = vs[int(rng.uniform(0.02, 0.35) * last)]
        elif kind == "le":
            v = vs[int(rng.uniform(0.65, 0.98) * last)]
        elif kind == "eq":
            fat = sorted(x for x, m in cnt.items() if m * 8 >= len(vs))
            v = rng.choice(fat) if fat else vs[last // 2]
        else:
            v = rng.choice(vs)
        return "prd %s %d %d" % (kind, c, v)

    want = pool if pool else max(1, (nc + 1) // 2)
    out = []
    for _ in range(nq):
        near = rng.sample(range(k), min(k, want))
        picks = []
        seen_eq = seen_nu = False
        for _i in range(nc):
            kind = rng.choice(kinds)
            if kind == "eq" and seen_eq:
                kind = "ne"
            if kind == "nu" and seen_nu:
                kind = "nn"
            seen_eq = seen_eq or kind == "eq"
            picks.append((rng.choice(near), kind))
            if kind == "nu":
                seen_nu = True
        taken = {c for c, kd in picks if kd != "nu"}
        for i, (c, kd) in enumerate(picks):
            if kd != "nu":
                continue
            free = [x for x in range(k) if x not in taken]
            if free:
                picks[i] = (rng.choice(free), "nu")
                taken.add(picks[i][0])
            else:
                picks[i] = (c, "nn")
        out.append("qry")
        for c, kind in picks:
            out.append(one(c, kind))
        out.append("prj " + " ".join(str(c) for c in rng.sample(range(k), min(k, nproj))))
        out.append("end")
    return out


def _stats(layout, c):
    vs = []
    for ch in layout[c]:
        for v in ch["vals"]:
            if v is not None:
                vs.append(v)
    vs.sort()
    cnt = {}
    for v in vs:
        cnt[v] = cnt.get(v, 0) + 1
    return vs, cnt


def _build(rng, g, n, layout, cols, queries):
    lines = ["seg %d %d %d" % (g, n, len(layout))]
    for c, chunks in enumerate(layout):
        for ch in chunks:
            lines.append(_chunk_line(c, ch))
    lines.extend(queries)
    return lines


def _small(fam, rng):
    if fam == "plain":
        g, n, k = rng.choice((5, 10, 25)), rng.randint(40, 160), rng.randint(2, 4)
        cfg = dict(nullrate=0.0, dictrate=0.0, litrate=0.0, exactrate=1.0)
        lo, hi = 0, 0
        nq, nc, kinds, nproj, pool = rng.randint(1, 2), rng.randint(2, 4), ("ge", "le", "ne"), 2, 2
    elif fam == "widen":
        g, n, k = rng.choice((10, 25, 50)), rng.randint(40, 160), rng.randint(2, 4)
        cfg = dict(nullrate=0.05, dictrate=0.1, litrate=0.3, exactrate=0.1)
        lo, hi = 0, 0
        nq, nc, kinds, nproj, pool = rng.randint(1, 2), rng.randint(3, 4), ("ge", "le", "eq", "ne"), 2, 2
    elif fam == "dicts":
        g, n, k = rng.choice((5, 10)), rng.randint(40, 140), rng.randint(2, 4)
        cfg = dict(nullrate=0.06, dictrate=0.95, litrate=0.45, exactrate=0.6)
        lo, hi = 0, 0
        nq, nc, kinds, nproj, pool = rng.randint(1, 2), rng.randint(3, 5), ("ge", "le", "eq", "ne"), 2, 2
    elif fam == "nulls":
        g, n, k = rng.choice((5, 10, 25)), rng.randint(40, 140), rng.randint(2, 4)
        cfg = dict(nullrate=rng.choice((0.35, 0.6, 0.9)), dictrate=0.3, litrate=0.2,
                   exactrate=0.5)
        lo, hi = 0, 0
        nq, nc, kinds, nproj, pool = rng.randint(1, 2), rng.randint(3, 4), KINDS, 2, 2
    elif fam == "skew":
        g, n, k = rng.choice((10, 25)), rng.randint(60, 180), rng.randint(3, 5)
        cfg = dict(nullrate=0.08, dictrate=0.35, litrate=0.3, exactrate=0.5)
        lo, hi = -1, -1
        nq, nc, kinds, nproj, pool = rng.randint(1, 2), rng.randint(3, 5), KINDS, 3, 3
    elif fam == "tight":
        g, n, k = rng.choice((10, 25)), rng.randint(60, 180), rng.randint(3, 5)
        cfg = dict(nullrate=0.05, dictrate=0.3, litrate=0.25, exactrate=0.45)
        lo, hi = 0, 0
        nq, nc, kinds, nproj, pool = rng.randint(1, 2), rng.randint(4, 6), ("ge", "le", "eq"), 2, 2
    elif fam == "ties":
        g, n, k = 10, rng.randint(40, 120), rng.randint(2, 4)
        cfg = dict(nullrate=0.0, dictrate=0.2, litrate=0.2, exactrate=0.8)
        lo, hi = -2, -2
        nq, nc, kinds, nproj, pool = rng.randint(1, 2), rng.randint(3, 5), ("ge", "le"), 2, 2
    elif fam == "reuse":
        g, n, k = rng.choice((5, 10)), rng.randint(40, 140), rng.randint(2, 3)
        cfg = dict(nullrate=0.1, dictrate=0.8, litrate=0.3, exactrate=0.5)
        lo, hi = 0, 0
        nq, nc, kinds, nproj, pool = rng.randint(1, 2), rng.randint(3, 6), ("ge", "le", "eq", "ne"), 3, 2
    elif fam == "empty":
        g, n, k = rng.choice((10, 25)), rng.randint(40, 120), rng.randint(2, 4)
        cfg = dict(nullrate=0.2, dictrate=0.4, litrate=0.3, exactrate=0.6)
        lo, hi = 0, 0
        nq, nc, kinds, nproj, pool = rng.randint(1, 2), rng.randint(3, 4), KINDS, 2, 2
    else:
        g, n, k = rng.choice((5, 10, 25)), rng.randint(50, 140), rng.randint(2, 4)
        cfg = dict(nullrate=0.12, dictrate=0.4, litrate=0.3, exactrate=0.5)
        lo, hi = 0, 0
        nq, nc, kinds, nproj, pool = rng.randint(3, 4), rng.randint(3, 4), KINDS, 2, 2

    layout = []
    for c in range(k):
        if lo == 0:
            a, b = max(3, n // 8), max(5, n // 4)
        elif lo == -1:
            a = max(2, n // rng.choice((3, 6, 12)))
            b = max(a + 1, a * 2)
        else:
            a = b = max(4, n // 6)
        sizes = _parts(rng, a, b) if False else _parts(rng, n, a, b)
        base = rng.choice((0, 7, 40, 200))
        span = rng.choice((6, 12, 30, 90)) if fam != "ties" else 20
        layout.append(_column(rng, sizes, base, span, g=g, **cfg))

    qs = _queries(rng, layout, nq, nc, kinds, nproj, pool)
    if fam == "empty":
        qs = ["qry", "prd eq 0 999999", "prd ne 1 -5", "prj 0 1", "end"] + qs
    return _build(rng, g, n, layout, range(k), qs)


def _large(fam, rng):
    if fam == "wide":
        g, n, k = 25, 40000, 5
        lo, hi = 170, 230
        nq, nc, nproj, pool = 2, 5, 2, 3
        cfg = dict(nullrate=0.07, dictrate=0.3, litrate=0.3, exactrate=0.5)
    else:
        g, n, k = 25, 40000, 4
        lo, hi = 1700, 2300
        nq, nc, nproj, pool = 2, 7, 2, 2
        cfg = dict(nullrate=0.07, dictrate=0.2, litrate=0.4, exactrate=0.5)
    layout = []
    for c in range(k):
        sizes = _parts(rng, n, lo, hi)
        base = rng.choice((0, 50, 300))
        span = rng.choice((40, 120, 400))
        layout.append(_column(rng, sizes, base, span, g=g, **cfg))
    qs = _queries(rng, layout, nq, nc, KINDS, nproj, pool)
    return _build(rng, g, n, layout, range(k), qs)


def programs(seed, per):
    out = []
    for fam, big in FAMILIES:
        count = BIG if big else per
        for i in range(count):
            rng = _rng(seed, fam, i)
            lines = _large(fam, rng) if big else _small(fam, rng)
            out.append((fam, "%s-%03d" % (fam, i), lines))
    return out
