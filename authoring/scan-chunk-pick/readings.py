"""The wrong readings a competent solver can hold, as patches on the reference.

Each reading is the reference with one decision changed, built by a textual patch that has to
fire: a patch whose anchor is no longer in the reference raises at import, so a reading cannot
go quietly stale when the reference is rewritten.

`python tools/readingcheck.py scan-chunk-pick` runs every one against the enumerated set and
reports which are separated by it, which are only caught by generated segment files, and which
nothing separates at all.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "scan-chunk-pick"
REFERENCE = str(TASK / "solution")

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import cases  # noqa: E402
import gen  # noqa: E402
import host  # noqa: E402

_SRC = {p.name: p.read_text(encoding="utf-8") for p in (TASK / "solution").glob("*.py")}
_ENGINES = {}


def _patch(name, *pairs):
    text = _SRC[name]
    for old, new in pairs:
        if old not in text:
            raise AssertionError("anchor gone from %s: %r" % (name, old[:60]))
        text = text.replace(old, new, 1)
    return {name: text}


# The order readings are patches on a loop that rescans every pending pair after every step.
# It is exactly the reference's order, only slow, and it is the loop the probe agents wrote first,
# so a reading on the order is the change a solver would make to that loop. The enumerated and
# small generated files are all it ever runs on.
_RESCAN = """from scn import hdr, live, step


def bound(seg, st, ch, cond):
    return st.cnt[(cond.pos, ch.j)]


def run(seg, q, st, out):
    while True:
        best = None
        for cd in q.conds:
            done = st.done[cd.pos]
            for ch in seg.cols[cd.c]:
                j = ch.j
                if j in done:
                    continue
                have = live.count(st, cd.c, j)
                if have <= 0:
                    continue
                b = bound(seg, st, ch, cd)
                if b > have:
                    b = have
                if best is None or b < best[0]:
                    best = (b, cd, j)
        if best is None:
            return
        cd, j = best[1], best[2]
        step.decide(seg, q, st, cd, j, out)
        st.done[cd.pos].add(j)
        st.dirty.clear()
"""


def _loop(*pairs):
    text = _RESCAN
    for old, new in pairs:
        if old not in text:
            raise AssertionError("anchor gone from the rescan loop: %r" % old[:60])
        text = text.replace(old, new, 1)
    return {"pick.py": text}


def _join(*parts):
    out = {}
    for part in parts:
        for name, text in part.items():
            if name in out:
                raise AssertionError("two patches on %s; chain them instead" % name)
            out[name] = text
    return out


READINGS = {
    # --- page headers ------------------------------------------------------------------
    "hdr-bounds-exact": _patch(
        "hdr.py",
        ("    if pg.exact:\n        return pg.mn, pg.mx\n    w = seg.g - 1\n"
         "    return pg.mn - w, pg.mx + w",
         "    return pg.mn, pg.mx")),
    "hdr-pass-ignores-nulls": _patch(
        "hdr.py",
        ("    if pg.nulls:\n        return False\n    if k == \"nn\":\n        return True",
         "    if k == \"nn\":\n        return pg.nulls == 0")),
    "hdr-null-always-read": _patch(
        "hdr.py",
        ("def miss(seg, pg, cond):\n    k = cond.kind\n    if k == \"nu\":\n        return pg.nulls == 0",
         "def miss(seg, pg, cond):\n    k = cond.kind\n    if k == \"nu\":\n        return False"),
        ("def allsat(seg, pg, cond):\n    k = cond.kind\n    if k == \"nu\":\n        return pg.nulls == pg.n",
         "def allsat(seg, pg, cond):\n    k = cond.kind\n    if k == \"nu\":\n        return False")),
    "hdr-spread-floor": _patch(
        "hdr.py", ("    part = -(-have * room // span)", "    part = have * room // span")),
    "hdr-spread-open": _patch(
        "hdr.py", ("        room = hi - v + 1", "        room = hi - v"),
        ("        room = v - lo + 1", "        room = v - lo")),

    # --- dictionaries ------------------------------------------------------------------
    "dic-fallback-used": _patch(
        "dct.py", ("    return ch.enc == \"d\" and pg.form == \"i\"", "    return ch.enc == \"d\"")),
    "dic-charge-each": _patch(
        "dct.py",
        ("    key = (ch.c, ch.j)\n    if key not in st.mem.dread:\n        st.mem.dread.add(key)\n"
         "        out.rd(ch.c, ch.j)",
         "    st.mem.dread.add((ch.c, ch.j))\n    out.rd(ch.c, ch.j)")),
    "dic-keep-ignores-nulls": _patch(
        "step.py", ("            if verdict == \"keep\" and pg.nulls == 0:",
                    "            if verdict == \"keep\":")),
    "dic-answers-null": _patch(
        "step.py", ("        if vals is None and cond.kind not in (\"nn\", \"nu\") and dct.usable(ch, pg):",
                    "        if vals is None and dct.usable(ch, pg):")),
    "dic-drop-needs-nulls": _patch(
        "dct.py", ("    if good == 0:\n        return \"drop\"",
                   "    if good == 0 and all(p.nulls == 0 for p in ch.pages):\n        return \"drop\"")),
    "pg-dict-all-pages": _patch(
        "dct.py", ("    return ch.enc == \"d\" and pg.form == \"i\"",
                   "    return ch.enc == \"d\" and all(p.form == \"i\" for p in ch.pages)")),
    "pg-dict-keep-chunk-nulls": _patch(
        "step.py", ("            if verdict == \"keep\" and pg.nulls == 0:",
                    "            if verdict == \"keep\" and all(p.nulls == 0 for p in ch.pages):")),

    # --- pages ---------------------------------------------------------------------------
    "pg-whole-chunk-read": _patch(
        "step.py",
        ("        if vals is None:\n            vals = load(seg, q, st, ch, pg, out)\n",
         "        if vals is None:\n            for other in ch.pages:\n"
         "                if (c, j, other.p) not in st.mem.vals:\n"
         "                    got = load(seg, q, st, ch, other, out)\n"
         "                    if other is pg:\n                        vals = got\n")),
    "pg-count-all-or-nothing": _patch(
        "live.py",
        ("    for cd in q.conds:\n        if cd.c == ch.c:\n"
         "            st.cnt[(cd.pos, ch.j)] += exact(st, cd, pg) - hdr.guess(seg, pg, cd)\n",
         "    whole = all((p.c, p.j, p.p) in st.mem.vals for p in ch.pages)\n"
         "    for cd in q.conds:\n        if cd.c == ch.c:\n"
         "            if whole:\n"
         "                st.cnt[(cd.pos, ch.j)] = sum(exact(st, cd, p) for p in ch.pages)\n"),
        ("            t = 0\n            for pg in ch.pages:\n"
         "                if (pg.c, pg.j, pg.p) in mem.vals:\n",
         "            t = 0\n            whole = all((p.c, p.j, p.p) in mem.vals for p in ch.pages)\n"
         "            for pg in ch.pages:\n"
         "                if whole:\n")),

    # --- the order -----------------------------------------------------------------------
    "ord-fixed-sweep": {"pick.py": """from scn import hdr, live, step


def run(seg, q, st, out):
    order = []
    for cd in q.conds:
        tot = 0
        for ch in seg.cols[cd.c]:
            for pg in ch.pages:
                tot += hdr.guess(seg, pg, cd)
        order.append((tot, cd.pos, cd))
    order.sort(key=lambda t: (t[0], t[1]))
    for _tot, _pos, cd in order:
        for ch in seg.cols[cd.c]:
            if live.count(st, cd.c, ch.j) <= 0:
                continue
            step.decide(seg, q, st, cd, ch.j, out)
            st.done[cd.pos].add(ch.j)
"""},
    "ord-column-sum": {"pick.py": """from scn import live, step


def run(seg, q, st, out):
    while True:
        chosen = None
        best = 0
        target = 0
        for cd in q.conds:
            done = st.done[cd.pos]
            tot = 0
            first = -1
            for ch in seg.cols[cd.c]:
                have = live.count(st, cd.c, ch.j)
                if have <= 0:
                    continue
                if ch.j in done:
                    tot += have
                    continue
                if first < 0:
                    first = ch.j
                b = st.cnt[(cd.pos, ch.j)]
                tot += b if b < have else have
            if first < 0:
                continue
            if chosen is None or tot < best:
                chosen = cd
                best = tot
                target = first
        if chosen is None:
            return
        step.decide(seg, q, st, chosen, target, out)
        st.done[chosen.pos].add(target)
"""},
    "ord-no-cap": _loop(("                if b > have:\n                    b = have\n", "")),
    "ord-header-only": _loop(("    return st.cnt[(cond.pos, ch.j)]",
                              "    return sum(hdr.guess(seg, pg, cond) for pg in ch.pages)")),
    "ord-highest-chunk": _loop(("                if best is None or b < best[0]:",
                                "                if best is None or b <= best[0]:")),
    "ord-largest-first": _loop(("                if best is None or b < best[0]:",
                                "                if best is None or b > best[0]:")),
    # the heap, trusting a key it pushed before a read raised the score
    "ord-stale-key": _patch(
        "pick.py", ("        if s != score(st, cd, j):\n            continue\n", "")),
    # the heap, re-scoring only on deaths: a read never pushes its chunk again
    "ord-read-no-push": _patch(
        "live.py", ("            st.cnt[(cd.pos, ch.j)] += exact(st, cd, pg) - hdr.guess(seg, pg, cd)\n"
                    "    st.dirty.add((ch.c, ch.j))",
                    "            st.cnt[(cd.pos, ch.j)] += exact(st, cd, pg) - hdr.guess(seg, pg, cd)")),

    # --- what a read settles -------------------------------------------------------------
    "dec-one-cond": _join(
        _patch("live.py",
               ("def learn(st, q, ch, pg):", "def learn(st, q, ch, pg, only=None):"),
               ("    for cd in q.conds:\n        if cd.c == ch.c:\n"
                "            st.cnt[(cd.pos, ch.j)] +=",
                "    for cd in q.conds:\n        if cd.c == ch.c and (only is None or cd is only):\n"
                "            st.cnt[(cd.pos, ch.j)] +=")),
        _patch("step.py",
               ("def load(seg, q, st, ch, pg, out):", "def load(seg, q, st, ch, pg, out, only=None):"),
               ("    live.learn(st, q, ch, pg)", "    live.learn(st, q, ch, pg, only)"),
               ("            vals = load(seg, q, st, ch, pg, out)",
                "            vals = load(seg, q, st, ch, pg, out, cond)"))),
    "dec-hits-live-only": _patch(
        "live.py",
        ("        for v in st.mem.vals[(pg.c, pg.j, pg.p)]:\n            if rd.sat(cd, v):",
         "        for i, v in enumerate(st.mem.vals[(pg.c, pg.j, pg.p)]):\n"
         "            if st.alive[pg.start + i] and rd.sat(cd, v):")),

    # --- rows carrying an update, and deleted rows ---------------------------------------
    "upd-drop-takes-moved": _patch(
        "step.py", ("        if hdr.miss(seg, pg, cond):\n            dead.extend(held)\n            continue",
                    "        if hdr.miss(seg, pg, cond):\n            dead.extend(held)\n"
                    "            dead.extend(moved)\n            continue")),
    "upd-keep-trusts-moved": _patch(
        "step.py",
        ("        dead.extend(r for r in moved if not rd.sat(cond, up[r]))\n        if not held:\n"
         "            continue\n",
         "        if not held:\n            dead.extend(r for r in moved if not rd.sat(cond, up[r]))\n"
         "            continue\n        if not hdr.allsat(seg, pg, cond):\n"
         "            dead.extend(r for r in moved if not rd.sat(cond, up[r]))\n")),
    "upd-read-anyway": _patch(
        "step.py", ("        if not held:\n            continue", "        if not held and not moved:\n            continue")),
    "upd-merge-on-read": _patch(
        "step.py",
        ("    vals = rd.values(ch, pg)\n",
         "    vals = list(rd.values(ch, pg))\n    up = seg.up[ch.c]\n"
         "    for i in range(pg.n):\n        if pg.start + i in up:\n"
         "            vals[i] = up[pg.start + i]\n"),
        ("        if not held:\n            continue", "        if not held and not moved:\n            continue")),
    "upd-count-current": _patch(
        "live.py",
        ("        for v in st.mem.vals[(pg.c, pg.j, pg.p)]:\n            if rd.sat(cd, v):",
         "        up = st.seg.up[pg.c]\n"
         "        for i, v in enumerate(st.mem.vals[(pg.c, pg.j, pg.p)]):\n"
         "            if pg.start + i in up:\n                v = up[pg.start + i]\n"
         "            if rd.sat(cd, v):")),
    "del-still-alive": _patch(
        "live.py", ("    for r in seg.gone:\n        st.alive[r] = 0\n", "")),
    "del-still-counted": _patch(
        "live.py", ("            counts.append(sum(alive[ch.start:ch.start + ch.n]))",
                    "            counts.append(ch.n)"),
        ("            alive[r] = 0\n            for c, own in st.own.items():",
         "            alive[r] = 0\n            for c, own in st.own.items():\n"
         "                if r in st.seg.gone:\n                    continue")),

    # --- the file's memory ---------------------------------------------------------------
    "mem-none": _patch("live.py", ("    st.mem = mem\n", "    st.mem = fresh(seg)\n")),
    "mem-no-exact-start": _patch(
        "live.py",
        ("                if (pg.c, pg.j, pg.p) in mem.vals:\n                    t += exact(st, cd, pg)\n"
         "                else:\n                    t += hdr.guess(seg, pg, cd)",
         "                t += hdr.guess(seg, pg, cd)"),
        ("    for cd in q.conds:\n        if cd.c == ch.c:\n"
         "            st.cnt[(cd.pos, ch.j)] += exact(st, cd, pg) - hdr.guess(seg, pg, cd)\n",
         "    for cd in q.conds:\n        if cd.c == ch.c and (ch.c, ch.j, pg.p, cd.pos) not in st.hit:\n"
         "            st.cnt[(cd.pos, ch.j)] += exact(st, cd, pg) - hdr.guess(seg, pg, cd)\n")),
    "mem-charge-per-query": _patch("live.py", ("    st.mem = mem\n", "    st.mem = mem\n    mem.dread = set()\n")),
    "mem-report-not-kept": _patch(
        "proj.py",
        ("from scn import dct, hdr, live, step", "from scn import dct, hdr, live, rd, step"),
        ("        vals = step.load(seg, q, st, ch, pg, out)",
         "        out.dc(ch.c, ch.j, pg.p)\n        vals = rd.values(ch, pg)")),

    # --- the report pass -----------------------------------------------------------------
    "prj-all-pages": _patch("proj.py", ("                if held:\n", "                if True:\n")),
    "prj-reads-moved": _patch("proj.py", ("                if held:\n", "                if held or moved:\n")),
    "prj-reads-pinned": _patch(
        "proj.py", ("        fixed, v = hdr.pinned(seg, pg)\n        if fixed:\n"
                    "            return (0, 0) if v is None else (len(held), v * len(held))\n", "")),
    "prj-pinned-ignores-widen": _patch(
        "hdr.py", ("    lo, hi = bounds(seg, pg)\n    if lo == hi:\n        return True, lo",
                   "    if pg.mn == pg.mx:\n        return True, pg.mn")),
    "prj-no-whole-sum": _patch(
        "proj.py", ("        if len(held) == pg.n:\n            return pg.n - pg.nulls, pg.sum\n", "")),
    "prj-whole-ignores-deletes": _patch(
        "proj.py", ("        if len(held) == pg.n:",
                    "        if len(held) == sum(1 for r in range(pg.start, pg.start + pg.n)\n"
                    "                            if r not in seg.gone):")),
    "prj-whole-ignores-updates": _patch(
        "proj.py", ("        if len(held) == pg.n:",
                    "        if sum(st.alive[pg.start:pg.start + pg.n]) == pg.n:")),
    "prj-no-one-entry": _patch(
        "proj.py", ("        if dct.single(ch, pg):\n            dct.charge(ch, st, out)\n"
                    "            return len(held), ch.dic[0] * len(held)\n", "")),
    "prj-one-entry-with-nulls": _patch(
        "dct.py", ("    return usable(ch, pg) and len(ch.dic) == 1 and pg.nulls == 0",
                   "    return usable(ch, pg) and len(ch.dic) == 1")),
    "prj-one-entry-fallback": _patch(
        "dct.py", ("    return usable(ch, pg) and len(ch.dic) == 1 and pg.nulls == 0",
                   "    return ch.enc == \"d\" and len(ch.dic) == 1 and pg.nulls == 0")),
    "prj-one-entry-free": _patch(
        "proj.py", ("            dct.charge(ch, st, out)\n            return len(held), ch.dic[0] * len(held)",
                    "            return len(held), ch.dic[0] * len(held)")),
    "prj-index-order": _patch("proj.py", ("    for c in q.cols:", "    for c in sorted(set(q.cols)):")),
    "prj-nulls-counted": _patch(
        "proj.py", ("        if v is not None:\n            nn += 1\n            tot += v",
                    "        nn += 1\n        if v is not None:\n            tot += v")),
    "prj-redecode": _patch(
        "proj.py", ("    vals = st.mem.vals.get((ch.c, ch.j, pg.p))\n    if vals is None:",
                    "    vals = None\n    if vals is None:")),
}


# The design the second easiness probe was run against, written in this grammar: every query
# starts over, a chunk is read whole, its dictionary is used only when every page is an index
# page and only when no page of it holds a null, a chunk's count turns exact only once every
# page is read, and the report pass never takes a page's sum from its header. Applied as one
# sequence of patches on the reference, each of which has to fire.
PREVIOUS = [
    ("live.py", "    st.mem = mem\n", "    st.mem = fresh(seg)\n"),
    ("live.py",
     "    for cd in q.conds:\n        if cd.c == ch.c:\n"
     "            st.cnt[(cd.pos, ch.j)] += exact(st, cd, pg) - hdr.guess(seg, pg, cd)\n",
     "    whole = all((p.c, p.j, p.p) in st.mem.vals for p in ch.pages)\n"
     "    for cd in q.conds:\n        if cd.c == ch.c:\n"
     "            if whole:\n"
     "                st.cnt[(cd.pos, ch.j)] = sum(exact(st, cd, p) for p in ch.pages)\n"),
    ("step.py",
     "        if vals is None:\n            vals = load(seg, q, st, ch, pg, out)\n",
     "        if vals is None:\n            for other in ch.pages:\n"
     "                if (c, j, other.p) not in st.mem.vals:\n"
     "                    got = load(seg, q, st, ch, other, out)\n"
     "                    if other is pg:\n                        vals = got\n"),
    ("step.py", "            if verdict == \"keep\" and pg.nulls == 0:",
     "            if verdict == \"keep\" and all(p.nulls == 0 for p in ch.pages):"),
    ("dct.py", "    return ch.enc == \"d\" and pg.form == \"i\"",
     "    return ch.enc == \"d\" and all(p.form == \"i\" for p in ch.pages)"),
    ("proj.py", "        if len(held) == pg.n:\n            return pg.n - pg.nulls, pg.sum\n", ""),
]


def previous():
    files = {}
    for name, old, new in PREVIOUS:
        text = files.get(name, _SRC[name])
        if old not in text:
            raise AssertionError("anchor gone from %s: %r" % (name, old[:60]))
        files[name] = text.replace(old, new, 1)
    return files


def _engine(policy):
    key = str(policy)
    if key not in _ENGINES:
        _ENGINES[key] = host.engine(host.tree(policy))
    return _ENGINES[key]


def run(policy, text):
    return _engine(policy).run(text if text.endswith("\n") else text + "\n")


def enumerated():
    return [(name, "\n".join(cases.prog(name)) + "\n") for name in cases.ORDER]


def generated(n):
    out = []
    per = max(1, n // 10)
    for fam, name, lines in gen.programs("readingcheck", per):
        if fam in ("wide", "deep"):
            continue
        out.append((name, "\n".join(lines) + "\n"))
    return out[:n]


def _blocks(lines):
    """The segment's chunks as (column, [line indexes of the chunk line and its pages])."""
    out = []
    for i, ln in enumerate(lines):
        f = ln.split()
        if not f:
            continue
        if f[0] == "ch":
            out.append((int(f[1]), [i]))
        elif f[0] == "pg":
            out[-1][1].append(i)
    return out


def _size(lines, block):
    return sum(int(lines[i].split()[1]) for i in block[1][1:])


def _cuts(lines):
    """Row counts where every column has a chunk boundary."""
    ends = {}
    for c, idx in _blocks(lines):
        ends.setdefault(c, [])
        prev = ends[c][-1] if ends[c] else 0
        ends[c].append(prev + _size(lines, (c, idx)))
    if not ends:
        return []
    common = set(ends[min(ends)])
    for c in ends:
        common &= set(ends[c])
    return sorted(common)


def reductions(text):
    lines = text.strip("\n").split("\n")
    heads = [i for i, ln in enumerate(lines) if ln.startswith("qry")]
    tails = [i for i, ln in enumerate(lines) if ln.startswith("end")]

    # drop a whole query
    if len(heads) > 1:
        for a, b in zip(heads, tails):
            yield "\n".join(lines[:a] + lines[b + 1:])

    # drop one condition, or one reported column
    for i, ln in enumerate(lines):
        if ln.startswith("prd") and sum(1 for x in lines if x.startswith("prd")) > 1:
            yield "\n".join(lines[:i] + lines[i + 1:])
        if ln.startswith("prj") and len(ln.split()) > 2:
            f = ln.split()
            for drop in range(1, len(f)):
                yield "\n".join(lines[:i] + [" ".join(f[:drop] + f[drop + 1:])] + lines[i + 1:])

    # drop one update or one delete
    for i, ln in enumerate(lines):
        if ln.startswith("up ") or ln.startswith("del "):
            yield "\n".join(lines[:i] + lines[i + 1:])

    head = lines[0].split()
    blocks = _blocks(lines)

    # keep only the first m rows, at a boundary every column shares
    if head and head[0] == "seg":
        n = int(head[2])
        for cut in _cuts(lines):
            if cut >= n:
                continue
            drop = set()
            seen = {}
            for c, idx in blocks:
                at = seen.get(c, 0)
                if at >= cut:
                    drop.update(idx)
                seen[c] = at + _size(lines, (c, idx))
            kept = ["seg %s %d %s" % (head[1], cut, head[3])]
            for i, ln in enumerate(lines[1:], 1):
                if i in drop:
                    continue
                f = ln.split()
                if f[0] == "up" and int(f[2]) >= cut:
                    continue
                if f[0] == "del" and int(f[1]) >= cut:
                    continue
                kept.append(ln)
            yield "\n".join(kept)

    # drop a column entirely, renumbering the ones above it
    if head and head[0] == "seg":
        k = int(head[3])
        if k > 1:
            for gone in range(k):
                skip = set()
                for c, idx in blocks:
                    if c == gone:
                        skip.update(idx)
                out = ["seg %s %s %d" % (head[1], head[2], k - 1)]
                ok = True
                for i, ln in enumerate(lines[1:], 1):
                    if i in skip:
                        continue
                    f = ln.split()
                    if f[0] == "ch":
                        c = int(f[1])
                        f[1] = str(c - 1 if c > gone else c)
                        out.append(" ".join(f))
                    elif f[0] == "up":
                        c = int(f[1])
                        if c == gone:
                            continue
                        f[1] = str(c - 1 if c > gone else c)
                        out.append(" ".join(f))
                    elif f[0] == "prd":
                        c = int(f[2])
                        if c == gone:
                            ok = False
                            break
                        f[2] = str(c - 1 if c > gone else c)
                        out.append(" ".join(f))
                    elif f[0] == "prj":
                        keep = [int(x) for x in f[1:] if int(x) != gone]
                        if not keep:
                            ok = False
                            break
                        out.append("prj " + " ".join(str(c - 1 if c > gone else c) for c in keep))
                    else:
                        out.append(ln)
                if ok:
                    yield "\n".join(out)
