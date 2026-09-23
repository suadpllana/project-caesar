"""The sealed model: what a segment file must print, worked out a second time.

Written against the contract rather than against the reference, and deliberately not shaped
like it. The reference splits the engine over six modules, keeps its scores in a heap that
tolerates stale entries and maintains every condition's count on every chunk incrementally as
pages are read. This is one module; the pending pairs sit in a segment tree of exact minima laid
out in tie-break order, and a chunk's count is summed afresh from its pages every time the chunk
is touched.

`expect(lines)` returns the lines `/app/run_scan.py` must print for that segment file.

A column is chunks and a chunk is pages. What a page header, a page read and a chunk's dictionary
describe is the page as written. A row's value in a column is its update when it has one, else
what its page holds; a deleted row is never alive. What a query reads or consults is remembered
for the rest of the file and printed only the first time.

A pair (condition, chunk) is applied page by page, in page order:

  1  live rows carrying an update in the column are tested on their new value, for nothing.
  2  a page with no live row that it still supplies is passed over: nothing consulted or read.
  3  otherwise those rows are put to the page header's two sound tests, in this order: no row
     of the page matches (they die), every row matches (they stay). A widened header means the
     recorded pair was rounded inward to a multiple of g, so the usable pair is pushed out by
     g - 1.
  4  a page read already settles them from its values, with nothing printed.
  5  a comparison on an `i` page consults the chunk's dictionary, charged once per chunk per
     file; no entry matching kills them, every entry matching keeps them if the page holds no
     null; anything else reads the page. is-null and is-not-null never consult a dictionary,
     and neither does a `v` page.
  6  otherwise the page is read, which settles the exact count of every condition of the query
     over that column on that page, over the page as written, and the rows are filtered.

The order: the pending pair expected to leave the fewest rows alive, that being the smaller of
the chunk's live rows and the condition's count on the chunk - summed over its pages, exact on a
page read in this query or an earlier one, the header's interpolation otherwise. Ties go to the
condition written earlier, then to the lower chunk. The report pass works the named columns in
order and each page in order; a page is wanted only when a live row takes its value from it, and
a wanted page not read already is answered by its header when every row is null, when it holds
no null and its bounds are one value, or when the wanted rows are every row of the page (its
non-null count and its sum); then by the dictionary (charged) for an `i` page with no null when
the dictionary has one entry; and by a read otherwise.
"""

MOD = 2305843009213693951
CMP = ("ge", "le", "eq", "ne")


def _num(tok):
    return None if tok == "-" else int(tok)


def _read(lines):
    seg = {"cols": [], "up": {}, "gone": set()}
    queries = []
    tail = [0] * 64
    cur = None
    rec = None
    for raw in lines:
        if not raw.strip():
            continue
        f = raw.split()
        if f[0] == "seg":
            seg["g"] = int(f[1])
            seg["n"] = int(f[2])
            seg["k"] = int(f[3])
            seg["cols"] = [[] for _ in range(seg["k"])]
        elif f[0] == "ch":
            c = int(f[1])
            rec = {"c": c, "j": len(seg["cols"][c]), "start": tail[c], "n": 0,
                   "dic": [int(t) for t in f[4:4 + int(f[3])]] if f[2] == "d" else None,
                   "pages": []}
            seg["cols"][c].append(rec)
        elif f[0] == "pg":
            n = int(f[1])
            form = f[7]
            toks = [_num(t) for t in f[8:8 + n]]
            if form == "i":
                vals = [None if t is None else rec["dic"][t] for t in toks]
            else:
                vals = toks
            c = rec["c"]
            page = {"c": c, "j": rec["j"], "p": len(rec["pages"]), "n": n,
                    "start": tail[c], "nulls": int(f[2]), "mn": _num(f[3]), "mx": _num(f[4]),
                    "exact": f[5] == "e", "sum": int(f[6]),
                    "dict": rec["dic"] is not None and form == "i", "vals": vals}
            tail[c] += n
            rec["n"] += n
            rec["pages"].append(page)
        elif f[0] == "up":
            seg["up"][(int(f[1]), int(f[2]))] = _num(f[3])
        elif f[0] == "del":
            seg["gone"].add(int(f[1]))
        elif f[0] == "qry":
            cur = {"conds": [], "cols": []}
        elif f[0] == "prd":
            cur["conds"].append({"kind": f[1], "c": int(f[2]),
                                 "v": int(f[3]) if len(f) > 3 else 0,
                                 "pos": len(cur["conds"])})
        elif f[0] == "prj":
            cur["cols"].extend(int(t) for t in f[1:])
        elif f[0] == "end":
            queries.append(cur)
            cur = None
    return seg, queries


def _span(g, page):
    if page["mn"] is None:
        return None
    if page["exact"]:
        return page["mn"], page["mx"]
    return page["mn"] - g + 1, page["mx"] + g - 1


def _holds(cond, v):
    k = cond["kind"]
    if v is None:
        return k == "nu"
    if k == "nu":
        return False
    if k == "nn":
        return True
    if k == "ge":
        return v >= cond["v"]
    if k == "le":
        return v <= cond["v"]
    if k == "eq":
        return v == cond["v"]
    return v != cond["v"]


def _none(g, page, cond):
    """The header proves that no row of the page satisfies the condition."""
    k = cond["kind"]
    if k == "nu":
        return page["nulls"] == 0
    seen = page["n"] - page["nulls"]
    if seen == 0:
        return True
    if k == "nn":
        return False
    lo, hi = _span(g, page)
    v = cond["v"]
    if k == "ge":
        return hi < v
    if k == "le":
        return lo > v
    if k == "eq":
        return v < lo or v > hi
    return lo == v and hi == v


def _all(g, page, cond):
    """The header proves that every row of the page satisfies the condition."""
    k = cond["kind"]
    if k == "nu":
        return page["nulls"] == page["n"]
    if page["nulls"] > 0:
        return False
    if k == "nn":
        return True
    lo, hi = _span(g, page)
    v = cond["v"]
    if k == "ge":
        return lo >= v
    if k == "le":
        return hi <= v
    if k == "eq":
        return lo == v and hi == v
    return hi < v or lo > v


def _spread(g, page, cond):
    """The interpolation the order is chosen on: non-null rows spread evenly over the bounds."""
    k = cond["kind"]
    if k == "nu":
        return page["nulls"]
    seen = page["n"] - page["nulls"]
    if k == "nn" or seen == 0:
        return seen
    lo, hi = _span(g, page)
    v = cond["v"]
    width = hi - lo + 1
    if k == "ge":
        room = hi - v + 1
    elif k == "le":
        room = v - lo + 1
    elif v < lo or v > hi:
        room = 0
    else:
        room = 1
    if room <= 0:
        return seen if k == "ne" else 0
    room = min(room, width)
    share = (seen * room + width - 1) // width
    return seen - share if k == "ne" else share


class _Tree:
    """Exact minimum over a fixed list of slots, each holding a key or nothing."""

    def __init__(self, size):
        n = 1
        while n < size:
            n *= 2
        self.n = n
        self.cell = [None] * (2 * n)

    def put(self, i, key):
        i += self.n
        self.cell[i] = key
        i //= 2
        while i:
            a, b = self.cell[2 * i], self.cell[2 * i + 1]
            if a is None:
                self.cell[i] = b
            elif b is None or a <= b:
                self.cell[i] = a
            else:
                self.cell[i] = b
            i //= 2

    def top(self):
        return self.cell[1]


def _one(seg, q, known, charged):
    g = seg["g"]
    cols = seg["cols"]
    ups = seg["up"]
    conds = q["conds"]
    flag = [0 if r in seg["gone"] else 1 for r in range(seg["n"])]
    used = []
    for cd in conds:
        if cd["c"] not in used:
            used.append(cd["c"])
    for c in q["cols"]:
        if c not in used:
            used.append(c)
    home = {}
    left = {}
    for c in used:
        pick = [0] * seg["n"]
        for rec in cols[c]:
            live = 0
            for r in range(rec["start"], rec["start"] + rec["n"]):
                pick[r] = rec["j"]
                live += flag[r]
            left[(c, rec["j"])] = live
        home[c] = pick

    out = []
    hits = {}
    settled = set()

    def exact(cd, page):
        key = (page["c"], page["j"], page["p"], cd["pos"])
        if key not in hits:
            hits[key] = sum(1 for v in page["vals"] if _holds(cd, v))
        return hits[key]

    def mark(cd, j):
        total = 0
        for page in cols[cd["c"]][j]["pages"]:
            if (page["c"], page["j"], page["p"]) in known:
                total += exact(cd, page)
            else:
                total += _spread(g, page, cd)
        return total

    base = []
    at = 0
    for cd in conds:
        base.append(at)
        at += len(cols[cd["c"]])
    tree = _Tree(max(1, at))
    by_col = {}
    for cd in conds:
        by_col.setdefault(cd["c"], []).append(cd)

    def refresh(c, j):
        for cd in by_col.get(c, ()):
            slot = base[cd["pos"]] + j
            room = left[(c, j)]
            if (cd["pos"], j) in settled or room <= 0:
                tree.put(slot, None)
            else:
                m = mark(cd, j)
                tree.put(slot, (room if room < m else m, slot, cd["pos"], j))

    touched = set()

    def strike(rows):
        for r in rows:
            if flag[r]:
                flag[r] = 0
                for c in used:
                    j = home[c][r]
                    left[(c, j)] -= 1
                    touched.add((c, j))

    def fetch(page):
        key = (page["c"], page["j"], page["p"])
        out.append("dc %d %d %d" % key)
        known.add(key)
        touched.add((page["c"], page["j"]))
        return page["vals"]

    def charge(rec):
        key = (rec["c"], rec["j"])
        if key not in charged:
            charged.add(key)
            out.append("rd %d %d" % key)

    for c in by_col:
        for rec in cols[c]:
            refresh(c, rec["j"])

    while True:
        best = tree.top()
        if best is None:
            break
        pos, j = best[2], best[3]
        cond = conds[pos]
        c = cond["c"]
        rec = cols[c][j]
        settled.add((pos, j))
        touched.add((c, j))
        doomed = []
        verdict = None
        for page in rec["pages"]:
            lo = page["start"]
            own = []
            for r in range(lo, lo + page["n"]):
                if not flag[r]:
                    continue
                if (c, r) in ups:
                    if not _holds(cond, ups[(c, r)]):
                        doomed.append(r)
                else:
                    own.append(r)
            if not own:
                continue
            if _none(g, page, cond):
                doomed.extend(own)
                continue
            if _all(g, page, cond):
                continue
            key = (c, j, page["p"])
            if key not in known and cond["kind"] in CMP and page["dict"]:
                if verdict is None:
                    charge(rec)
                    fit = sum(1 for v in rec["dic"] if _holds(cond, v))
                    verdict = "none" if fit == 0 else ("all" if fit == len(rec["dic"]) else "some")
                if verdict == "none":
                    doomed.extend(own)
                    continue
                if verdict == "all" and page["nulls"] == 0:
                    continue
            vals = page["vals"] if key in known else fetch(page)
            doomed.extend(r for r in own if not _holds(cond, vals[r - lo]))
        strike(doomed)
        for cc, jj in touched:
            refresh(cc, jj)
        touched.clear()

    kept = [r for r in range(seg["n"]) if flag[r]]
    h = 0
    for r in kept:
        h = (h * 1000003 + r + 1) % MOD
    out.append("sel %d %d" % (len(kept), h))

    for c in q["cols"]:
        good = 0
        total = 0
        for rec in cols[c]:
            for page in rec["pages"]:
                lo = page["start"]
                own = []
                for r in range(lo, lo + page["n"]):
                    if not flag[r]:
                        continue
                    if (c, r) in ups:
                        v = ups[(c, r)]
                        if v is not None:
                            good += 1
                            total += v
                    else:
                        own.append(r)
                if not own:
                    continue
                key = (c, rec["j"], page["p"])
                span = _span(g, page)
                if key in known:
                    vals = page["vals"]
                    for r in own:
                        v = vals[r - lo]
                        if v is not None:
                            good += 1
                            total += v
                elif page["nulls"] == page["n"]:
                    pass
                elif page["nulls"] == 0 and span[0] == span[1]:
                    good += len(own)
                    total += span[0] * len(own)
                elif len(own) == page["n"]:
                    good += page["n"] - page["nulls"]
                    total += page["sum"]
                elif page["dict"] and len(rec["dic"]) == 1 and page["nulls"] == 0:
                    charge(rec)
                    good += len(own)
                    total += rec["dic"][0] * len(own)
                else:
                    vals = fetch(page)
                    for r in own:
                        v = vals[r - lo]
                        if v is not None:
                            good += 1
                            total += v
        out.append("prj %d %d %d" % (c, good, total))
    return out


def expect(lines):
    seg, queries = _read(lines)
    known = set()
    charged = set()
    out = []
    for i, q in enumerate(queries):
        out.append("qry %d" % i)
        out.extend(_one(seg, q, known, charged))
    return out
