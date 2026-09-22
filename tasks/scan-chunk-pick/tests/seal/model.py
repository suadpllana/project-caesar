"""The sealed model: what a segment file must print, worked out a second time.

Written against the contract rather than against the reference, and deliberately not shaped
like it. The reference splits the engine over six modules, carries the survivors in a byte per
row with a per-chunk count maintained as rows die, and keeps the decoded values on the state
object. This is one module, holds the survivors as a flat list of flags with the counts in a
dict keyed by chunk, rebuilds the candidate list from scratch on every pass and keeps a chunk's
values and its per-condition hit counts together in one record.

`expect(lines)` returns the lines `/app/run_scan.py` must print for that segment file.

The rules, in the order they are applied to a chunk:

  1  the two header tests are sound and are asked first, in this order: the bounds and the
     null count prove no row matches, or they prove every row does. A widened header (the
     exactness flag is off) means the recorded pair was rounded inward to a multiple of the
     granularity, so the usable pair is the recorded one pushed out by g - 1.
  2  an already-read chunk is settled from its values, with nothing printed.
  3  a comparison over a chunk whose dictionary covers every row consults that dictionary,
     which is charged once per chunk however many conditions reach it; no entry matching
     drops the chunk, every entry matching with no nulls keeps it, anything else reads it.
     is-null and is-not-null are never answered from a dictionary.
  4  otherwise the chunk is read, which settles the exact count of every condition of the
     query over that column, and the condition being applied then filters it.

The order: the pending pair expected to leave the fewest rows alive, that being the smaller of
the chunk's surviving rows and the condition's count on it - the header's interpolation until
the chunk has been read, the exact count after. Ties go to the condition written earlier in the
query, then to the lower chunk number. Then the report pass, over the columns the query names
in the order it names them, reading only chunks that still hold a survivor and were not read
already.
"""

MOD = 2305843009213693951
CMP = ("ge", "le", "eq", "ne")


def _num(tok):
    return None if tok == "-" else int(tok)


def _read(lines):
    seg = {"cols": []}
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


def _one(seg, q):
    g = seg["g"]
    cols = seg["cols"]
    flag = [1] * seg["n"]
    used = []
    for cd in q["conds"]:
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
            for r in range(rec["start"], rec["start"] + rec["n"]):
                pick[r] = rec["j"]
            left[(c, rec["j"])] = rec["n"]
        home[c] = pick

    out = []
    hit = {}
    body = {}
    charged = set()
    settled = set()

    def strike(rows):
        for r in rows:
            if flag[r]:
                flag[r] = 0
                for c in used:
                    left[(c, home[c][r])] -= 1

    def wipe(rec):
        strike(range(rec["start"], rec["start"] + rec["n"]))

    def fetch(rec):
        out.append("dc %d %d" % (rec["c"], rec["j"]))
        vals = rec["vals"]
        body[(rec["c"], rec["j"])] = vals
        for other in q["conds"]:
            if other["c"] == rec["c"]:
                hit[(rec["c"], rec["j"], other["pos"])] = sum(
                    1 for v in vals if _holds(other, v))
        return vals

    def apply(cond, rec, vals):
        base = rec["start"]
        strike([base + i for i in range(rec["n"])
                if flag[base + i] and not _holds(cond, vals[i])])

    while True:
        take = None
        for cond in q["conds"]:
            for rec in cols[cond["c"]]:
                if (cond["pos"], rec["j"]) in settled:
                    continue
                room = left[(cond["c"], rec["j"])]
                if room <= 0:
                    continue
                mark = hit.get((cond["c"], rec["j"], cond["pos"]))
                if mark is None:
                    mark = _spread(g, rec, cond)
                score = room if room < mark else mark
                if take is None or score < take[0]:
                    take = (score, cond, rec)
        if take is None:
            break
        cond, rec = take[1], take[2]
        settled.add((cond["pos"], rec["j"]))
        key = (cond["c"], rec["j"])
        if _none(g, rec, cond):
            wipe(rec)
            continue
        if _all(g, rec, cond):
            continue
        vals = body.get(key)
        if vals is None:
            if cond["kind"] in CMP and rec["dic"] is not None and rec["whole"]:
                if key not in charged:
                    charged.add(key)
                    out.append("rd %d %d" % (cond["c"], rec["j"]))
                fit = sum(1 for v in rec["dic"] if _holds(cond, v))
                if fit == 0:
                    wipe(rec)
                    continue
                if fit == len(rec["dic"]) and rec["nulls"] == 0:
                    continue
            vals = fetch(rec)
        apply(cond, rec, vals)

    kept = [r for r in range(seg["n"]) if flag[r]]
    h = 0
    for r in kept:
        h = (h * 1000003 + r + 1) % MOD
    out.append("sel %d %d" % (len(kept), h))

    for c in q["cols"]:
        for rec in cols[c]:
            if left[(c, rec["j"])] > 0 and (c, rec["j"]) not in body:
                fetch(rec)
        pick = home[c]
        good = 0
        total = 0
        for r in kept:
            rec = cols[c][pick[r]]
            v = body[(c, rec["j"])][r - rec["start"]]
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
