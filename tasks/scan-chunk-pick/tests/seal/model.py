"""The sealed model: what a segment file must print, worked out a second time.

Written against the contract rather than against the reference, and deliberately not shaped
like it. The reference splits the engine over six modules, keeps its scores in a heap that
tolerates stale entries, and splits a chunk's live rows into those with and without an update
before it decides anything. This is one module; the pending pairs sit in a segment tree of
exact minima indexed in tie-break order, so a score that moves in either direction is simply
written in place; and every row is resolved on its own against the update map.

`expect(lines)` returns the lines `/app/run_scan.py` must print for that segment file.

What a chunk's header, dictionary and exact counts describe is the chunk as written. A row's
value in a column is its update when it has one, else what its chunk holds; a deleted row is
never alive. The rules, in the order they are applied to a pair (condition, chunk):

  1  live rows carrying an update in the column are tested on their new value, for nothing.
  2  if no live row still takes its value from the chunk, that is all: nothing is consulted.
  3  otherwise those rows are put to the two sound header tests, in this order: no row the
     chunk holds matches (they die), every row matches (they stay). A widened header means the
     recorded pair was rounded inward to a multiple of g, so the usable pair is pushed out by
     g - 1.
  4  an already-read chunk settles them from its values, with nothing printed.
  5  a comparison over a chunk whose dictionary covers every row consults it, charged once per
     chunk; no entry matching kills them, every entry matching with no nulls keeps them,
     anything else reads the chunk. is-null and is-not-null never consult a dictionary.
  6  otherwise the chunk is read, which settles the exact count of every condition of the
     query over that column, over the chunk as written, and the rows are filtered.

The order: the pending pair expected to leave the fewest rows alive, that being the smaller of
the chunk's live rows and the condition's count on it - the header's interpolation until the
chunk has been read, the exact count after. Ties go to the condition written earlier, then to
the lower chunk. The report pass works the named columns in order; a chunk is wanted only when
a surviving row takes its value from it, and a wanted chunk that is not read already is served
by its header when every row is null or its low equals its high with no nulls, by its
dictionary (charged) when that has one entry, no overflow and no nulls, and by a read
otherwise.
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
            n = int(f[2])
            rec = {"c": c, "j": len(seg["cols"][c]), "n": n, "start": tail[c],
                   "nulls": int(f[3]), "mn": _num(f[4]), "mx": _num(f[5]),
                   "exact": f[6] == "e"}
            tail[c] += n
            if f[7] == "p":
                rec["vals"] = [_num(t) for t in f[8:8 + n]]
                rec["dic"] = None
                rec["whole"] = False
            else:
                k = int(f[8])
                dic = [int(t) for t in f[9:9 + k]]
                body = f[9 + k:9 + k + n]
                vals = []
                whole = True
                for tok in body:
                    if tok == "-":
                        vals.append(None)
                    elif tok[0] == "*":
                        vals.append(int(tok[1:]))
                        whole = False
                    else:
                        vals.append(dic[int(tok)])
                rec["vals"] = vals
                rec["dic"] = dic
                rec["whole"] = whole
            seg["cols"][c].append(rec)
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


def _span(g, rec):
    if rec["mn"] is None:
        return None
    if rec["exact"]:
        return rec["mn"], rec["mx"]
    return rec["mn"] - g + 1, rec["mx"] + g - 1


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


def _none(g, rec, cond):
    """The header proves that no row of the chunk satisfies the condition."""
    k = cond["kind"]
    if k == "nu":
        return rec["nulls"] == 0
    seen = rec["n"] - rec["nulls"]
    if seen == 0:
        return True
    if k == "nn":
        return False
    lo, hi = _span(g, rec)
    v = cond["v"]
    if k == "ge":
        return hi < v
    if k == "le":
        return lo > v
    if k == "eq":
        return v < lo or v > hi
    return lo == v and hi == v


def _all(g, rec, cond):
    """The header proves that every row of the chunk satisfies the condition."""
    k = cond["kind"]
    if k == "nu":
        return rec["nulls"] == rec["n"]
    if rec["nulls"] > 0:
        return False
    if k == "nn":
        return True
    lo, hi = _span(g, rec)
    v = cond["v"]
    if k == "ge":
        return lo >= v
    if k == "le":
        return hi <= v
    if k == "eq":
        return lo == v and hi == v
    return hi < v or lo > v


def _spread(g, rec, cond):
    """The interpolation the order is chosen on: live rows spread evenly over the bounds."""
    k = cond["kind"]
    if k == "nu":
        return rec["nulls"]
    seen = rec["n"] - rec["nulls"]
    if k == "nn" or seen == 0:
        return seen
    lo, hi = _span(g, rec)
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


def _one(seg, q):
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
    hit = {}
    body = {}
    charged = set()
    settled = set()

    # slot of pair (condition position, chunk) in tie-break order
    base = []
    at = 0
    for cd in conds:
        base.append(at)
        at += len(cols[cd["c"]])
    tree = _Tree(max(1, at))
    by_col = {}
    for cd in conds:
        by_col.setdefault(cd["c"], []).append(cd)

    def score(cd, j):
        rec = cols[cd["c"]][j]
        room = left[(cd["c"], j)]
        mark = hit.get((cd["c"], j, cd["pos"]))
        if mark is None:
            mark = _spread(g, rec, cd)
        return room if room < mark else mark

    def refresh(c, j):
        for cd in by_col.get(c, ()):
            slot = base[cd["pos"]] + j
            if (cd["pos"], j) in settled or left[(c, j)] <= 0:
                tree.put(slot, None)
            else:
                tree.put(slot, (score(cd, j), slot, cd["pos"], j))

    touched = set()

    def strike(rows):
        for r in rows:
            if flag[r]:
                flag[r] = 0
                for c in used:
                    j = home[c][r]
                    left[(c, j)] -= 1
                    touched.add((c, j))

    def fetch(rec):
        out.append("dc %d %d" % (rec["c"], rec["j"]))
        vals = rec["vals"]
        body[(rec["c"], rec["j"])] = vals
        for other in conds:
            if other["c"] == rec["c"]:
                hit[(rec["c"], rec["j"], other["pos"])] = sum(
                    1 for v in vals if _holds(other, v))
        touched.add((rec["c"], rec["j"]))
        return vals

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
        lo = rec["start"]
        doomed = []
        own = []
        for r in range(lo, lo + rec["n"]):
            if not flag[r]:
                continue
            if (c, r) in ups:
                if not _holds(cond, ups[(c, r)]):
                    doomed.append(r)
            else:
                own.append(r)
        if own:
            if _none(g, rec, cond):
                doomed.extend(own)
            elif not _all(g, rec, cond):
                vals = body.get((c, j))
                verdict = "read"
                if vals is None and cond["kind"] in CMP and rec["dic"] is not None \
                        and rec["whole"]:
                    charge(rec)
                    fit = sum(1 for v in rec["dic"] if _holds(cond, v))
                    if fit == 0:
                        verdict = "none"
                    elif fit == len(rec["dic"]) and rec["nulls"] == 0:
                        verdict = "all"
                if verdict == "none":
                    doomed.extend(own)
                elif verdict == "read":
                    if vals is None:
                        vals = fetch(rec)
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
        known = {}
        for rec in cols[c]:
            j = rec["j"]
            lo = rec["start"]
            wanted = any(flag[r] and (c, r) not in ups for r in range(lo, lo + rec["n"]))
            if not wanted:
                continue
            if (c, j) in body:
                known[j] = body[(c, j)]
                continue
            span = _span(g, rec)
            if rec["nulls"] == rec["n"]:
                known[j] = [None] * rec["n"]
            elif rec["nulls"] == 0 and span[0] == span[1]:
                known[j] = [span[0]] * rec["n"]
            elif rec["dic"] is not None and rec["whole"] and len(rec["dic"]) == 1 \
                    and rec["nulls"] == 0:
                charge(rec)
                known[j] = [rec["dic"][0]] * rec["n"]
            else:
                known[j] = fetch(rec)
        pick = home[c]
        good = 0
        total = 0
        for r in kept:
            if (c, r) in ups:
                v = ups[(c, r)]
            else:
                j = pick[r]
                v = known[j][r - cols[c][j]["start"]]
            if v is not None:
                good += 1
                total += v
        out.append("prj %d %d %d" % (c, good, total))
    return out


def expect(lines):
    seg, queries = _read(lines)
    out = []
    for i, q in enumerate(queries):
        out.append("qry %d" % i)
        out.extend(_one(seg, q))
    return out
