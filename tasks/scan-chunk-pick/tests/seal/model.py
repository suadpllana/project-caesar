"""The sealed model: what a segment file must print, worked out a second time.

Written against the contract rather than against the reference, and deliberately not shaped
like it. The reference splits the engine over six modules, keeps a set of open pages per
condition, keeps its scores in a heap that tolerates stale entries, maintains every condition's
count on every chunk incrementally, and classifies the report's pages into kinds. This is one
module. It asks each row's fate afresh from what is known; the pending pairs sit in a segment
tree of exact minima laid out in tie-break order; a chunk's count is summed afresh from its pages
every time the chunk is touched; and the report's reads are found by asking of each page, in so
many words, whether the line could be told without it if every other page that could be read
were read.

`expect(lines)` returns the lines `/app/run_scan.py` must print for that segment file.

A column is chunks and a chunk is pages. A chunk line carries the sum of the non-null values of
all its pages; a page line carries its row count, null count and recorded bounds, and no sum.
Everything a page or a chunk says describes it as written. A row's value in a column is its
update when it has one, else what its page holds; a deleted row is never alive. What a query
reads or consults is remembered for the rest of the file and printed only the first time.

What is known of a live row's value in a column: its update; otherwise its page's header (the
two sound tests, with widened bounds when the recorded pair was rounded inward), the page's
values once read, and for an `i` page the chunk's dictionary once consulted (no entry matching a
comparison fails it; every entry matching passes it on a page holding no null). A row dies the
moment that shows it fails a condition - at the start of the query and after every consult and
every read.

A pair (condition, chunk) is pending while a live row takes its value from one of the chunk's
pages without the condition settled for it. The pending pair expected to leave the fewest rows
alive is applied next: the smaller of the chunk's live rows and the condition's count on the
chunk, summed over its pages - exact on a page read in this query or an earlier one, the header's
interpolation otherwise. Ties go to the condition written earlier, then to the lower chunk.
Applying it takes the chunk's pages in order; a page still holding such a row consults the
dictionary first for a comparison on an `i` page whose dictionary is not yet consulted, and is
read if such a row remains.

The report works the named columns in order. From each page it needs how many of the live rows
taking their value from it are non-null and their sum. Known: a page read; every value null on a
page whose rows are all null; every non-null value equal on a page whose bounds are one value,
or on an `i` page of a consulted one-entry dictionary; the null count of every page; and each
chunk's sum. A page is read only for its live rows and only when the line cannot be told without
it even with every other page that could be read. A one-entry dictionary not yet consulted is
consulted before its chunk's reads when one of its `i` pages supplies a live row and knowing it
spares a read. Reads come in chunk and page order.
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
                   "total": int(f[3]),
                   "dic": [int(t) for t in f[5:5 + int(f[4])]] if f[2] == "d" else None,
                   "pages": []}
            seg["cols"][c].append(rec)
        elif f[0] == "pg":
            n = int(f[1])
            form = f[6]
            toks = [_num(t) for t in f[7:7 + n]]
            if form == "i":
                vals = [None if t is None else rec["dic"][t] for t in toks]
            else:
                vals = toks
            c = rec["c"]
            page = {"c": c, "j": rec["j"], "p": len(rec["pages"]), "n": n,
                    "start": tail[c], "nulls": int(f[2]), "mn": _num(f[3]), "mx": _num(f[4]),
                    "exact": f[5] == "e",
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
    where = {}
    for c in used:
        pick = [0] * seg["n"]
        at = [None] * seg["n"]
        for rec in cols[c]:
            for page in rec["pages"]:
                for r in range(page["start"], page["start"] + page["n"]):
                    pick[r] = rec["j"]
                    at[r] = page
        home[c] = pick
        where[c] = at
    by_col = {}
    for cd in conds:
        by_col.setdefault(cd["c"], []).append(cd)

    out = []
    hits = {}

    def fate(cd, r):
        """What is known says about row r under condition cd: True, False, or None."""
        c = cd["c"]
        if (c, r) in ups:
            return _holds(cd, ups[(c, r)])
        page = where[c][r]
        key = (c, page["j"], page["p"])
        if key in known:
            return _holds(cd, page["vals"][r - page["start"]])
        if _none(g, page, cd):
            return False
        if _all(g, page, cd):
            return True
        if (c, page["j"]) in charged and page["dict"] and cd["kind"] in CMP:
            dic = cols[c][page["j"]]["dic"]
            fit = sum(1 for v in dic if _holds(cd, v))
            if fit == 0:
                return False
            if fit == len(dic) and page["nulls"] == 0:
                return True
        return None

    touched = set()

    def strike(rows):
        for r in rows:
            if flag[r]:
                flag[r] = 0
                for c in used:
                    touched.add((c, home[c][r]))

    def sweep(c, lo, hi):
        """Put rows lo..hi-1 to every condition over column c; the ones any fails die."""
        doomed = []
        for r in range(lo, hi):
            if flag[r]:
                for cd in by_col.get(c, ()):
                    if fate(cd, r) is False:
                        doomed.append(r)
                        break
        strike(doomed)

    for c in by_col:
        sweep(c, 0, seg["n"])

    def left(c, j):
        rec = cols[c][j]
        return sum(flag[r] for r in range(rec["start"], rec["start"] + rec["n"]))

    def waiting(cd, j):
        c = cd["c"]
        rec = cols[c][j]
        for r in range(rec["start"], rec["start"] + rec["n"]):
            if flag[r] and (c, r) not in ups and fate(cd, r) is None:
                return True
        return False

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

    def refresh(c, j):
        for cd in by_col.get(c, ()):
            slot = base[cd["pos"]] + j
            if not waiting(cd, j):
                tree.put(slot, None)
            else:
                room = left(c, j)
                m = mark(cd, j)
                tree.put(slot, (room if room < m else m, slot, cd["pos"], j))

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
            touched.add(key)

    for c in by_col:
        for rec in cols[c]:
            refresh(c, rec["j"])
    touched.clear()

    while True:
        best = tree.top()
        if best is None:
            break
        pos, j = best[2], best[3]
        cond = conds[pos]
        c = cond["c"]
        rec = cols[c][j]
        for page in rec["pages"]:
            lo = page["start"]
            hi = lo + page["n"]

            def open_rows():
                return [r for r in range(lo, hi)
                        if flag[r] and (c, r) not in ups and fate(cond, r) is None]

            if not open_rows():
                continue
            if cond["kind"] in CMP and page["dict"] and (c, j) not in charged:
                charge(rec)
                sweep(c, rec["start"], rec["start"] + rec["n"])
                if not open_rows():
                    continue
            fetch(page)
            sweep(c, lo, hi)
        touched.add((c, j))
        for cc, jj in touched:
            refresh(cc, jj)
        touched.clear()

    kept = [r for r in range(seg["n"]) if flag[r]]
    h = 0
    for r in kept:
        h = (h * 1000003 + r + 1) % MOD
    out.append("sel %d %d" % (len(kept), h))

    def figures(rec, dk, reads):
        """Whether the chunk's part of the line is told if the pages in `reads` are read too."""
        c = rec["c"]
        total_known = True
        unknown_whole = []
        other_unknown = False
        for page in rec["pages"]:
            key = (c, rec["j"], page["p"])
            lo = page["start"]
            own = [r for r in range(lo, lo + page["n"]) if flag[r] and (c, r) not in ups]
            if key in known or key in reads or page["nulls"] == page["n"]:
                continue
            span = _span(g, page)
            same = span is not None and span[0] == span[1]
            if not same and dk and page["dict"] and len(rec["dic"]) == 1:
                same = True
            if same:
                if own and len(own) < page["n"] and page["nulls"] > 0:
                    total_known = False
                continue
            if not own:
                other_unknown = True
            elif len(own) == page["n"]:
                unknown_whole.append(page)
            else:
                total_known = False
        if unknown_whole and other_unknown:
            total_known = False
        return total_known

    def readable(rec):
        c = rec["c"]
        got = []
        for page in rec["pages"]:
            key = (c, rec["j"], page["p"])
            lo = page["start"]
            if key in known:
                continue
            if any(flag[r] and (c, r) not in ups for r in range(lo, lo + page["n"])):
                got.append(key)
        return got

    def owed(rec, dk):
        cand = readable(rec)
        need = []
        for key in cand:
            others = set(k for k in cand if k != key)
            if not figures(rec, dk, others):
                need.append(key)
        return need

    for c in q["cols"]:
        good = 0
        total = 0
        for rec in cols[c]:
            j = rec["j"]
            dk = (c, j) in charged
            if not dk and rec["dic"] is not None and len(rec["dic"]) == 1:
                supplies = False
                for page in rec["pages"]:
                    lo = page["start"]
                    if page["dict"] and any(flag[r] and (c, r) not in ups
                                            for r in range(lo, lo + page["n"])):
                        supplies = True
                if supplies and len(owed(rec, True)) < len(owed(rec, False)):
                    charge(rec)
                    dk = True
            for key in sorted(owed(rec, dk)):
                fetch(cols[c][key[1]]["pages"][key[2]])
            rest = rec["total"]
            whole_left = 0
            whole_count = 0
            for page in rec["pages"]:
                key = (c, j, page["p"])
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
                span = _span(g, page)
                same = None
                if span is not None and span[0] == span[1]:
                    same = span[0]
                elif dk and page["dict"] and len(rec["dic"]) == 1:
                    same = rec["dic"][0]
                if key in known:
                    vals = page["vals"]
                    rest -= sum(v for v in vals if v is not None)
                    for r in own:
                        v = vals[r - lo]
                        if v is not None:
                            good += 1
                            total += v
                elif page["nulls"] == page["n"]:
                    pass
                elif same is not None:
                    seen = page["n"] - page["nulls"]
                    rest -= same * seen
                    if len(own) == page["n"]:
                        good += seen
                        total += same * seen
                    else:
                        good += len(own)
                        total += same * len(own)
                elif len(own) == page["n"]:
                    whole_left += 1
                    whole_count += page["n"] - page["nulls"]
            if whole_left:
                good += whole_count
                total += rest
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
