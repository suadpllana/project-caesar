"""Segment files generated inside the verifier, from a seed drawn after the agent is gone.

Sixteen families, each shaped at one part of the mechanism rather than drawn at random: inexact
headers that only the widening rule survives, dictionaries with and without an overflow list,
chunk partitions that disagree between columns, conditions that collapse the survivor counts
early so every later estimate moves, estimates built to tie, reports over columns a condition
already read, chunks whose every row carries an update, report columns whose header or
one-entry dictionary already fixes a chunk's values, heavy deletion, chunks whose even spread sits far below what a read finds, and the two scale shapes
the execution limit is set against.

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
    ("moved", False),
    ("pinned", False),
    ("gone", False),
    ("rise", False),
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


def _column(rng, sizes, base, span, nullrate, dictrate, litrate, exactrate, g,
            constrate=0.0, voidrate=0.0, lean=0.0):
    """Values and chunk headers for one column.

    A constant chunk holds one value; half of them sit on a multiple of the granularity, so a
    widened header can round onto them while a one-entry dictionary still names the value, and
    a quarter carry nulls, so the one entry no longer covers every row. A void chunk holds
    nothing but nulls. `lean` piles a chunk's values into the top of its range behind one low
    outlier, so the even spread the order starts from sits far below the exact count a read
    finds.
    """
    chunks = []
    for n in sizes:
        vals = []
        roll = rng.random()
        if roll < voidrate:
            vals = [None] * n
        elif roll < voidrate + constrate:
            v = base + rng.randrange(span)
            if rng.random() < 0.5:
                v = max(g, (v // g) * g)
            vals = [v] * n
            if n > 2 and rng.random() < 0.25:
                for i in rng.sample(range(n), rng.randint(1, n // 2)):
                    vals[i] = None
        elif roll < voidrate + constrate + lean:
            vals = [base]
            top = max(1, span // 6)
            for _ in range(n - 1):
                vals.append(base + span - 1 - rng.randrange(top))
        for _ in range(n - len(vals)):
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
        if seen and len(seen) <= 12 and (rng.random() < dictrate
                                          or (len(seen) == 1 and rng.random() < 0.7)):
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


def _overlay(rng, layout, n, uprate, fullrate, delrate, voidrate=0.0):
    """Updates and deletes. Some chunks have every row updated, so nothing alive takes its
    value from them; the rest get scattered updates. Deleted rows are scattered too, and a
    whole run of them is sometimes cut out."""
    lines = []
    for c, chunks in enumerate(layout):
        vs = sorted({v for ch in chunks for v in ch["vals"] if v is not None}) or [0]
        at = 0
        for ch in chunks:
            full = rng.random() < fullrate
            for i in range(ch["n"]):
                if full or rng.random() < uprate:
                    v = None if rng.random() < 0.1 else rng.choice(vs)
                    lines.append("up %d %d %s" % (c, at + i, "-" if v is None else str(v)))
            at += ch["n"]
    gone = set()
    for r in range(n):
        if rng.random() < delrate:
            gone.add(r)
    if voidrate and rng.random() < voidrate:
        a = rng.randrange(n)
        gone.update(range(a, min(n, a + rng.randint(3, max(4, n // 8)))))
    lines.extend("del %d" % r for r in sorted(gone))
    return lines


def _build(rng, g, n, layout, cols, queries, over=()):
    lines = ["seg %d %d %d" % (g, n, len(layout))]
    for c, chunks in enumerate(layout):
        for ch in chunks:
            lines.append(_chunk_line(c, ch))
    lines.extend(over)
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


# overlay per family: (update rate, whole-chunk update rate, delete rate, deleted-run chance)
_OV = {
    "plain": (0.0, 0.0, 0.0, 0.0),
    "widen": (0.03, 0.04, 0.02, 0.0),
    "dicts": (0.04, 0.06, 0.02, 0.0),
    "nulls": (0.04, 0.05, 0.02, 0.0),
    "skew": (0.05, 0.08, 0.03, 0.2),
    "tight": (0.04, 0.06, 0.02, 0.0),
    "ties": (0.02, 0.03, 0.0, 0.0),
    "reuse": (0.05, 0.08, 0.02, 0.0),
    "empty": (0.04, 0.05, 0.03, 0.3),
    "multi": (0.05, 0.08, 0.03, 0.2),
    "moved": (0.2, 0.35, 0.02, 0.0),
    "pinned": (0.05, 0.1, 0.02, 0.0),
    "gone": (0.03, 0.05, 0.2, 0.8),
    "rise": (0.05, 0.05, 0.02, 0.0),
}


def _small(fam, rng):
    more = {}
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
    elif fam == "moved":
        g, n, k = rng.choice((5, 10, 25)), rng.randint(50, 150), rng.randint(2, 4)
        cfg = dict(nullrate=0.08, dictrate=0.45, litrate=0.3, exactrate=0.5)
        lo, hi = 0, 0
        nq, nc, kinds, nproj, pool = rng.randint(1, 2), rng.randint(3, 5), KINDS, 2, 2
    elif fam == "pinned":
        g, n, k = rng.choice((5, 10, 25)), rng.randint(50, 150), rng.randint(3, 5)
        cfg = dict(nullrate=0.06, dictrate=0.35, litrate=0.3, exactrate=0.5)
        more = dict(constrate=0.3, voidrate=0.12)
        lo, hi = 0, 0
        nq, nc, kinds, nproj, pool = rng.randint(1, 2), rng.randint(2, 3), KINDS, 4, 2
    elif fam == "gone":
        g, n, k = rng.choice((5, 10, 25)), rng.randint(50, 150), rng.randint(2, 4)
        cfg = dict(nullrate=0.1, dictrate=0.4, litrate=0.3, exactrate=0.5)
        more = dict(constrate=0.1, voidrate=0.05)
        lo, hi = 0, 0
        nq, nc, kinds, nproj, pool = rng.randint(1, 2), rng.randint(3, 4), KINDS, 3, 2
    elif fam == "rise":
        g, n, k = rng.choice((5, 10)), rng.randint(60, 160), rng.randint(2, 3)
        cfg = dict(nullrate=0.04, dictrate=0.2, litrate=0.3, exactrate=0.8)
        more = dict(lean=0.6)
        lo, hi = 0, 0
        nq, nc, kinds, nproj, pool = rng.randint(1, 2), rng.randint(4, 6), ("ge", "le", "ne"), 2, 1
    else:
        g, n, k = rng.choice((5, 10, 25)), rng.randint(50, 140), rng.randint(2, 4)
        cfg = dict(nullrate=0.12, dictrate=0.4, litrate=0.3, exactrate=0.5)
        more = dict(constrate=0.08, voidrate=0.04)
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
        sizes = _parts(rng, n, a, b)
        base = rng.choice((0, 7, 40, 200))
        span = rng.choice((6, 12, 30, 90)) if fam != "ties" else 20
        layout.append(_column(rng, sizes, base, span, g=g, **cfg, **more))

    up, full, dl, run = _OV[fam]
    over = _overlay(rng, layout, n, up, full, dl, run)
    qs = _queries(rng, layout, nq, nc, kinds, min(k, nproj), pool)
    if fam == "empty":
        qs = ["qry", "prd eq 0 999999", "prd ne 1 -5", "prj 0 1", "end"] + qs
    return _build(rng, g, n, layout, range(k), qs, over)


def _large(fam, rng):
    if fam == "wide":
        g, n, k = 25, 60000, 5
        lo, hi = 10, 24
        nq, nc, nproj, pool = 2, 8, 3, 4
        kinds = ("ge", "le", "ne", "nn")
        cfg = dict(nullrate=0.07, dictrate=0.3, litrate=0.3, exactrate=0.5)
        more = dict(constrate=0.03, voidrate=0.01)
        ov = (0.02, 0.03, 0.01, 0.0)
    else:
        g, n, k = 25, 40000, 4
        lo, hi = 1700, 2300
        nq, nc, nproj, pool = 2, 7, 2, 2
        kinds = KINDS
        cfg = dict(nullrate=0.07, dictrate=0.2, litrate=0.4, exactrate=0.5)
        more = {}
        ov = (0.03, 0.0, 0.01, 0.0)
    layout = []
    for c in range(k):
        sizes = _parts(rng, n, lo, hi)
        base = rng.choice((0, 50, 300))
        span = rng.choice((40, 120, 400))
        layout.append(_column(rng, sizes, base, span, g=g, **cfg, **more))
    over = _overlay(rng, layout, n, *ov)
    qs = _queries(rng, layout, nq, nc, kinds, nproj, pool)
    return _build(rng, g, n, layout, range(k), qs, over)


def programs(seed, per):
    out = []
    for fam, big in FAMILIES:
        count = BIG if big else per
        for i in range(count):
            rng = _rng(seed, fam, i)
            lines = _large(fam, rng) if big else _small(fam, rng)
            out.append((fam, "%s-%03d" % (fam, i), lines))
    return out
