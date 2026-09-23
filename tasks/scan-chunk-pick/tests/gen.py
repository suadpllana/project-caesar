"""Segment files generated inside the verifier, from a seed drawn after the agent is gone.

Sixteen families, each shaped at one part of the mechanism rather than drawn at random: inexact
headers that only the widening rule survives, dictionary chunks whose later pages fell back to
plain values, chunk partitions that disagree between columns, conditions that collapse the live
counts early so every later estimate moves, estimates built to tie, chunks whose every row
carries an update, report columns whose page header or one-entry dictionary already answers,
pages that stay whole so their header sum answers and pages that a delete or an update breaks,
heavy deletion, skewed pages whose interpolation sits far below what a read finds, files whose
later queries run on what earlier ones read, and the two scale shapes the execution limit is
set against.

`programs(seed, per)` returns (family, name, lines) with `per` files of every small family and
three of each large one. The same call is made by the worker, which runs them, and by the
grader, which grades them against the sealed model, so both see the same population.
"""
import hashlib
import random

KINDS = ("ge", "le", "eq", "ne", "nn", "nu")

# (name, large) - the two scale families ship three files each whatever `per` is.
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
    """Cut n rows into runs of between lo and hi rows."""
    out = []
    left = n
    while left > 0:
        take = min(left, rng.randint(lo, hi))
        if left - take < lo and left - take > 0:
            take = left
        out.append(take)
        left -= take
    return out


def _header(vals, exactrate, g, rng):
    live = [v for v in vals if v is not None]
    nulls = len(vals) - len(live)
    if not live:
        return nulls, None, None, True, 0
    mn, mx = min(live), max(live)
    exact = rng.random() < exactrate
    if not exact:
        lo = ((mn + g - 1) // g) * g
        hi = (mx // g) * g
        if lo <= hi:
            mn, mx = lo, hi
        else:
            exact = True
    return nulls, mn, mx, exact, sum(live)


def _values(rng, n, base, span, nullrate, style, g):
    if style == "void":
        return [None] * n
    if style == "const":
        v = base + rng.randrange(span)
        if rng.random() < 0.5:
            v = max(g, (v // g) * g)
        vals = [v] * n
        if n > 2 and rng.random() < 0.25:
            for i in rng.sample(range(n), rng.randint(1, n // 2)):
                vals[i] = None
        return vals
    if style == "lean":
        top = max(1, span // 6)
        vals = [base] + [base + span - 1 - rng.randrange(top) for _ in range(n - 1)]
        rng.shuffle(vals)
        return vals
    return [None if rng.random() < nullrate else base + rng.randrange(span) for _ in range(n)]


def _column(rng, sizes, base, span, g, nullrate, dictrate, fallrate, exactrate, pagelo,
            pagehi, constrate=0.0, voidrate=0.0, lean=0.0, pagevoid=0.0):
    """Values, pages and headers for one column.

    A dictionary chunk keeps its first pages as indexes into the dictionary, which holds exactly
    the values those pages carry; from some page on it may fall back to plain values, as a writer
    does once its dictionary grows too large, and a fallback page can hold values the dictionary
    lacks. A constant chunk holds one value (a quarter of them with nulls), half of them on a
    multiple of the granularity so a widened header rounds onto it; a void chunk holds nothing but
    nulls; a lean chunk piles its values into the top of its range behind one low outlier.
    """
    chunks = []
    for n in sizes:
        roll = rng.random()
        style = "mixed"
        if roll < voidrate:
            style = "void"
        elif roll < voidrate + constrate:
            style = "const"
        elif roll < voidrate + constrate + lean:
            style = "lean"
        vals = _values(rng, n, base, span, nullrate, style, g)
        cuts = _parts(rng, n, pagelo, pagehi)
        pages = []
        at = 0
        for m in cuts:
            pv = vals[at:at + m]
            if style == "mixed" and rng.random() < pagevoid:
                pv = [None] * m
            pages.append(pv)
            at += m
        seen = sorted({v for pv in pages for v in pv if v is not None})
        enc = "p"
        keep = len(pages)
        if seen and (rng.random() < dictrate or (len(seen) == 1 and rng.random() < 0.7)):
            enc = "d"
            if len(pages) > 1 and rng.random() < fallrate:
                keep = rng.randint(1, len(pages) - 1)
        dic = sorted({v for pv in pages[:keep] for v in pv if v is not None}) if enc == "d" else None
        if enc == "d" and not dic:
            enc, dic, keep = "p", None, len(pages)
        if enc == "d" and keep < len(pages):
            extra = [base + span + rng.randrange(1, 7) for _ in range(2)]
            for pv in pages[keep:]:
                for i in range(len(pv)):
                    if pv[i] is not None and rng.random() < 0.3:
                        pv[i] = rng.choice(extra)
        out = []
        for i, pv in enumerate(pages):
            nulls, mn, mx, exact, s = _header(pv, exactrate, g, rng)
            form = "i" if enc == "d" and i < keep else "v"
            out.append({"vals": pv, "nulls": nulls, "mn": mn, "mx": mx, "exact": exact,
                        "sum": s, "form": form})
        chunks.append({"enc": enc, "dic": dic, "pages": out})
    return chunks


def _chunk_lines(c, ch):
    if ch["enc"] == "p":
        lines = ["ch %d p" % c]
    else:
        lines = ["ch %d d %d %s" % (c, len(ch["dic"]), " ".join(str(v) for v in ch["dic"]))]
    at = {v: i for i, v in enumerate(ch["dic"] or ())}
    for pg in ch["pages"]:
        head = ["pg", str(len(pg["vals"])), str(pg["nulls"]),
                "-" if pg["mn"] is None else str(pg["mn"]),
                "-" if pg["mx"] is None else str(pg["mx"]),
                "e" if pg["exact"] else "w", str(pg["sum"]), pg["form"]]
        if pg["form"] == "i":
            body = ["-" if v is None else str(at[v]) for v in pg["vals"]]
        else:
            body = ["-" if v is None else str(v) for v in pg["vals"]]
        lines.append(" ".join(head + body))
    return lines


def _all_vals(layout, c):
    return [v for ch in layout[c] for pg in ch["pages"] for v in pg["vals"]]


def _stats(layout, c):
    vs = sorted(v for v in _all_vals(layout, c) if v is not None)
    cnt = {}
    for v in vs:
        cnt[v] = cnt.get(v, 0) + 1
    return vs, cnt


def _overlay(rng, layout, n, uprate, fullrate, delrate, runrate=0.0):
    """Updates and deletes. Some chunks have every row updated, so nothing alive takes its
    value from them; the rest get scattered updates. Deleted rows are scattered too, and a
    whole run of them is sometimes cut out."""
    lines = []
    for c, chunks in enumerate(layout):
        vs = sorted({v for v in _all_vals(layout, c) if v is not None}) or [0]
        at = 0
        for ch in chunks:
            size = sum(len(pg["vals"]) for pg in ch["pages"])
            full = rng.random() < fullrate
            for i in range(size):
                if full or rng.random() < uprate:
                    v = None if rng.random() < 0.1 else rng.choice(vs)
                    lines.append("up %d %d %s" % (c, at + i, "-" if v is None else str(v)))
            at += size
    gone = set()
    for r in range(n):
        if rng.random() < delrate:
            gone.add(r)
    if runrate and rng.random() < runrate:
        a = rng.randrange(n)
        gone.update(range(a, min(n, a + rng.randint(3, max(4, n // 8)))))
    lines.extend("del %d" % r for r in sorted(gone))
    return lines


def _build(g, n, layout, queries, over=()):
    lines = ["seg %d %d %d" % (g, n, len(layout))]
    for c, chunks in enumerate(layout):
        for ch in chunks:
            lines.extend(_chunk_lines(c, ch))
    lines.extend(over)
    lines.extend(queries)
    return lines


def _queries(rng, layout, nq, nc, kinds, nproj, pool=None, share=0.0):
    """Queries over the layout. With `share`, a later query reuses columns an earlier one
    already read, so what the file remembers decides what it prints."""
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
    last_near = None
    for _ in range(nq):
        if last_near is not None and rng.random() < share:
            near = list(last_near)
        else:
            near = rng.sample(range(k), min(k, want))
        last_near = near
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
    "pinned": (0.03, 0.08, 0.01, 0.0),
    "gone": (0.03, 0.05, 0.2, 0.8),
    "rise": (0.05, 0.05, 0.02, 0.0),
}


def _small(fam, rng):
    more = {}
    share = 0.5
    if fam == "plain":
        g, n, k = rng.choice((5, 10, 25)), rng.randint(40, 160), rng.randint(2, 4)
        cfg = dict(nullrate=0.0, dictrate=0.0, fallrate=0.0, exactrate=1.0)
        nq, nc, kinds, nproj, pool = rng.randint(1, 3), rng.randint(2, 4), ("ge", "le", "ne"), 2, 2
    elif fam == "widen":
        g, n, k = rng.choice((10, 25, 50)), rng.randint(40, 160), rng.randint(2, 4)
        cfg = dict(nullrate=0.05, dictrate=0.1, fallrate=0.3, exactrate=0.1)
        nq, nc, kinds, nproj, pool = rng.randint(1, 3), rng.randint(3, 4), ("ge", "le", "eq", "ne"), 2, 2
    elif fam == "dicts":
        g, n, k = rng.choice((5, 10)), rng.randint(40, 140), rng.randint(2, 4)
        cfg = dict(nullrate=0.06, dictrate=0.95, fallrate=0.45, exactrate=0.6)
        nq, nc, kinds, nproj, pool = rng.randint(2, 3), rng.randint(3, 5), ("ge", "le", "eq", "ne"), 2, 2
    elif fam == "nulls":
        g, n, k = rng.choice((5, 10, 25)), rng.randint(40, 140), rng.randint(2, 4)
        cfg = dict(nullrate=rng.choice((0.35, 0.6, 0.9)), dictrate=0.3, fallrate=0.2,
                   exactrate=0.5)
        more = dict(pagevoid=0.1)
        nq, nc, kinds, nproj, pool = rng.randint(1, 3), rng.randint(3, 4), KINDS, 2, 2
    elif fam == "skew":
        g, n, k = rng.choice((10, 25)), rng.randint(60, 180), rng.randint(3, 5)
        cfg = dict(nullrate=0.08, dictrate=0.35, fallrate=0.3, exactrate=0.5)
        nq, nc, kinds, nproj, pool = rng.randint(1, 3), rng.randint(3, 5), KINDS, 3, 3
    elif fam == "tight":
        g, n, k = rng.choice((10, 25)), rng.randint(60, 180), rng.randint(3, 5)
        cfg = dict(nullrate=0.05, dictrate=0.3, fallrate=0.25, exactrate=0.45)
        nq, nc, kinds, nproj, pool = rng.randint(1, 3), rng.randint(4, 6), ("ge", "le", "eq"), 2, 2
    elif fam == "ties":
        g, n, k = 10, rng.randint(40, 120), rng.randint(2, 4)
        cfg = dict(nullrate=0.0, dictrate=0.2, fallrate=0.2, exactrate=0.8)
        nq, nc, kinds, nproj, pool = rng.randint(1, 3), rng.randint(3, 5), ("ge", "le"), 2, 2
    elif fam == "reuse":
        g, n, k = rng.choice((5, 10)), rng.randint(40, 140), rng.randint(2, 3)
        cfg = dict(nullrate=0.1, dictrate=0.8, fallrate=0.3, exactrate=0.5)
        share = 0.9
        nq, nc, kinds, nproj, pool = rng.randint(2, 4), rng.randint(3, 6), ("ge", "le", "eq", "ne"), 3, 2
    elif fam == "empty":
        g, n, k = rng.choice((10, 25)), rng.randint(40, 120), rng.randint(2, 4)
        cfg = dict(nullrate=0.2, dictrate=0.4, fallrate=0.3, exactrate=0.6)
        more = dict(pagevoid=0.1)
        nq, nc, kinds, nproj, pool = rng.randint(1, 3), rng.randint(3, 4), KINDS, 2, 2
    elif fam == "moved":
        g, n, k = rng.choice((5, 10, 25)), rng.randint(50, 150), rng.randint(2, 4)
        cfg = dict(nullrate=0.08, dictrate=0.45, fallrate=0.3, exactrate=0.5)
        nq, nc, kinds, nproj, pool = rng.randint(1, 3), rng.randint(3, 5), KINDS, 2, 2
    elif fam == "pinned":
        g, n, k = rng.choice((5, 10, 25)), rng.randint(50, 150), rng.randint(3, 5)
        cfg = dict(nullrate=0.06, dictrate=0.35, fallrate=0.3, exactrate=0.5)
        more = dict(constrate=0.3, voidrate=0.12, pagevoid=0.08)
        nq, nc, kinds, nproj, pool = rng.randint(1, 3), rng.randint(1, 3), KINDS, 4, 2
    elif fam == "gone":
        g, n, k = rng.choice((5, 10, 25)), rng.randint(50, 150), rng.randint(2, 4)
        cfg = dict(nullrate=0.1, dictrate=0.4, fallrate=0.3, exactrate=0.5)
        more = dict(constrate=0.1, voidrate=0.05)
        nq, nc, kinds, nproj, pool = rng.randint(1, 3), rng.randint(2, 4), KINDS, 3, 2
    elif fam == "rise":
        g, n, k = rng.choice((5, 10)), rng.randint(60, 160), rng.randint(2, 3)
        cfg = dict(nullrate=0.04, dictrate=0.2, fallrate=0.3, exactrate=0.8)
        more = dict(lean=0.6)
        nq, nc, kinds, nproj, pool = rng.randint(1, 3), rng.randint(4, 6), ("ge", "le", "ne"), 2, 1
    else:
        g, n, k = rng.choice((5, 10, 25)), rng.randint(50, 140), rng.randint(2, 4)
        cfg = dict(nullrate=0.12, dictrate=0.4, fallrate=0.3, exactrate=0.5)
        more = dict(constrate=0.08, voidrate=0.04, pagevoid=0.05)
        share = 0.7
        nq, nc, kinds, nproj, pool = rng.randint(2, 4), rng.randint(3, 4), KINDS, 2, 2

    layout = []
    for c in range(k):
        if fam == "skew":
            a = max(2, n // rng.choice((3, 6, 12)))
            b = max(a + 1, a * 2)
        elif fam == "ties":
            a = b = max(4, n // 6)
        else:
            a, b = max(3, n // 8), max(5, n // 4)
        sizes = _parts(rng, n, a, b)
        base = rng.choice((0, 7, 40, 200))
        span = rng.choice((6, 12, 30, 90)) if fam != "ties" else 20
        pl = max(1, min(sizes) // 3)
        layout.append(_column(rng, sizes, base, span, g=g, pagelo=pl, pagehi=max(pl, pl * 3),
                              **cfg, **more))

    up, full, dl, run = _OV[fam]
    over = _overlay(rng, layout, n, up, full, dl, run)
    qs = _queries(rng, layout, nq, nc, kinds, min(k, nproj), pool, share)
    if fam == "empty":
        qs = ["qry", "prd eq 0 999999", "prd ne 1 -5", "prj 0 1", "end"] + qs
    return _build(g, n, layout, qs, over)


def _large(fam, rng):
    if fam == "wide":
        g, n, k = 25, 60000, 5
        lo, hi, plo, phi = 16, 40, 4, 12
        nq, nc, nproj, pool = 3, 8, 3, 4
        kinds = ("ge", "le", "ne", "nn")
        cfg = dict(nullrate=0.07, dictrate=0.3, fallrate=0.3, exactrate=0.5)
        more = dict(constrate=0.03, voidrate=0.01)
        ov = (0.02, 0.03, 0.01, 0.0)
    else:
        g, n, k = 25, 40000, 4
        lo, hi, plo, phi = 1700, 2300, 150, 400
        nq, nc, nproj, pool = 3, 7, 2, 2
        kinds = KINDS
        cfg = dict(nullrate=0.07, dictrate=0.2, fallrate=0.4, exactrate=0.5)
        more = {}
        ov = (0.03, 0.0, 0.01, 0.0)
    layout = []
    for c in range(k):
        sizes = _parts(rng, n, lo, hi)
        base = rng.choice((0, 50, 300))
        span = rng.choice((40, 120, 400))
        layout.append(_column(rng, sizes, base, span, g=g, pagelo=plo, pagehi=phi, **cfg, **more))
    over = _overlay(rng, layout, n, *ov)
    qs = _queries(rng, layout, nq, nc, kinds, nproj, pool, 0.6)
    return _build(g, n, layout, qs, over)


def programs(seed, per):
    out = []
    for fam, big in FAMILIES:
        count = BIG if big else per
        for i in range(count):
            rng = _rng(seed, fam, i)
            lines = _large(fam, rng) if big else _small(fam, rng)
            out.append((fam, "%s-%03d" % (fam, i), lines))
    return out
