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


def _chain(*edits):
    """Several patches on one or more files, applied in order, each of which has to fire."""
    out = {}
    for name, old, new in edits:
        text = out.get(name, _SRC[name])
        if old not in text:
            raise AssertionError("anchor gone from %s: %r" % (name, old[:60]))
        out[name] = text.replace(old, new, 1)
    return out


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
            for ch in seg.cols[cd.c]:
                j = ch.j
                if j in st.done[cd.pos] or not live.pending(st, cd, j):
                    continue
                have = live.count(st, cd.c, j)
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


_STEP_BODY = """        if cond.kind not in ("nn", "nu") and dct.usable(ch, pg) and not dct.known(st, ch):
            dct.charge(ch, st, out)
            live.settle_dict(st, ch)
            if key not in opened or not live.held(st, c, pg):
                continue
        vals = load(seg, st, ch, pg, out)
        live.settle_read(st, ch, pg, vals)
"""

# Free facts acting only when their own condition's pair reaches the page, the settlement every
# first engine wrote: shared by the four late-settlement readings below.
_LATE_START = ("live.py", """                for cd in cds:
                    if vals is not None:
                        s = pg.start
                        dead.update(r for r in rows if not rd.sat(cd, vals[r - s]))
                    elif hdr.miss(seg, pg, cd):
                        dead.update(rows)
                    elif hdr.allsat(seg, pg, cd):
                        pass
                    elif dk and cd.kind not in ("nn", "nu") and dct.usable(ch, pg):
                        v = dct.verdict(ch, cd)
                        if v == "drop":
                            dead.update(rows)
                        elif v != "keep" or pg.nulls:
                            st.open[cd.pos].add((ch.j, pg.p))
                    else:
                        st.open[cd.pos].add((ch.j, pg.p))""", """                for cd in cds:
                    st.open[cd.pos].add((ch.j, pg.p))""")
_LATE_STEP = ("step.py", _STEP_BODY, """        if hdr.miss(seg, pg, cond):
            live.kill(st, live.held(st, c, pg))
            opened.discard(key)
            continue
        if hdr.allsat(seg, pg, cond):
            opened.discard(key)
            continue
        known = st.mem.vals.get((c, j, pg.p))
        if known is not None:
            s = pg.start
            live.kill(st, [r for r in live.held(st, c, pg) if not rd.sat(cond, known[r - s])])
            opened.discard(key)
            continue
        if cond.kind not in ("nn", "nu") and dct.usable(ch, pg):
            if not dct.known(st, ch):
                dct.charge(ch, st, out)
            v = dct.verdict(ch, cond)
            if v == "drop":
                live.kill(st, live.held(st, c, pg))
                opened.discard(key)
                continue
            if v == "keep" and pg.nulls == 0:
                opened.discard(key)
                continue
        vals = load(seg, st, ch, pg, out)
        s = pg.start
        live.kill(st, [r for r in live.held(st, c, pg) if not rd.sat(cond, vals[r - s])])
        opened.discard(key)
        live.settle_counts(st, ch, pg)
""")
_LATE_COUNTS = ("live.py", "def settle_dict(st, ch):", """def settle_counts(st, ch, pg):
    seg = st.seg
    for cd in st.on.get(ch.c, ()):
        st.cnt[(cd.pos, ch.j)] += exact(st, cd, pg) - hdr.guess(seg, pg, cd)
    st.dirty.add((ch.c, ch.j))


def settle_dict(st, ch):""")
_LATE_IMPORT = ("step.py", "from scn import dct, live, rd", "from scn import dct, hdr, live, rd")


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
    # the dictionary charged again by every pair that puts a page to it
    "dic-charge-each": _patch(
        "step.py",
        ("        if cond.kind not in (\"nn\", \"nu\") and dct.usable(ch, pg) and not dct.known(st, ch):",
         "        if (cond.kind not in (\"nn\", \"nu\") and dct.usable(ch, pg) and dct.known(st, ch)\n"
         "                and (id(st), cond.pos, j) not in _CHARGED):\n"
         "            _CHARGED.add((id(st), cond.pos, j))\n"
         "            out.rd(ch.c, ch.j)\n"
         "        if cond.kind not in (\"nn\", \"nu\") and dct.usable(ch, pg) and not dct.known(st, ch):\n"
         "            _CHARGED.add((id(st), cond.pos, j))"),
        ("from scn import dct, live, rd\n", "from scn import dct, live, rd\n\n_CHARGED = set()\n")),
    "dic-keep-ignores-nulls": _chain(
        ("live.py", "            elif pg.nulls == 0:\n                opened.discard(key)",
         "            else:\n                opened.discard(key)"),
        ("live.py", "                        elif v != \"keep\" or pg.nulls:",
         "                        elif v != \"keep\":")),
    "dic-answers-null": _chain(
        ("live.py", "        if cd.kind in (\"nn\", \"nu\"):\n            continue\n        v = dct.verdict(ch, cd)",
         "        v = dct.verdict(ch, cd)"),
        ("live.py", "                    elif dk and cd.kind not in (\"nn\", \"nu\") and dct.usable(ch, pg):",
         "                    elif dk and dct.usable(ch, pg):"),
        ("step.py", "        if cond.kind not in (\"nn\", \"nu\") and dct.usable(ch, pg) and not dct.known(st, ch):",
         "        if dct.usable(ch, pg) and not dct.known(st, ch):")),
    "dic-drop-needs-nulls": _patch(
        "dct.py", ("    if good == 0:\n        return \"drop\"",
                   "    if good == 0 and all(p.nulls == 0 for p in ch.pages):\n        return \"drop\"")),
    "pg-dict-all-pages": _patch(
        "dct.py", ("    return ch.enc == \"d\" and pg.form == \"i\"",
                   "    return ch.enc == \"d\" and all(p.form == \"i\" for p in ch.pages)")),
    "pg-dict-keep-chunk-nulls": _chain(
        ("live.py", "            elif pg.nulls == 0:\n                opened.discard(key)",
         "            elif all(p.nulls == 0 for p in ch.pages):\n                opened.discard(key)"),
        ("live.py", "                        elif v != \"keep\" or pg.nulls:",
         "                        elif v != \"keep\" or any(p.nulls for p in ch.pages):")),

    # --- pages ---------------------------------------------------------------------------
    "pg-whole-chunk-read": _patch(
        "step.py",
        ("        vals = load(seg, st, ch, pg, out)\n        live.settle_read(st, ch, pg, vals)\n",
         "        for other in ch.pages:\n"
         "            if (c, j, other.p) not in st.mem.vals:\n"
         "                live.settle_read(st, ch, other, load(seg, st, ch, other, out))\n")),
    "pg-count-all-or-nothing": _chain(
        ("live.py",
         "        st.cnt[(cd.pos, ch.j)] += exact(st, cd, pg) - hdr.guess(seg, pg, cd)\n",
         "        if all((p.c, p.j, p.p) in st.mem.vals for p in ch.pages):\n"
         "            st.cnt[(cd.pos, ch.j)] = sum(exact(st, cd, p) for p in ch.pages)\n"),
        ("live.py",
         "            t = 0\n            for pg in ch.pages:\n"
         "                if (pg.c, pg.j, pg.p) in mem.vals:\n",
         "            t = 0\n            whole = all((p.c, p.j, p.p) in mem.vals for p in ch.pages)\n"
         "            for pg in ch.pages:\n"
         "                if whole:\n")),
    "pg-read-consults-dict": _patch(
        "step.py",
        ("    out.dc(ch.c, ch.j, pg.p)\n    vals = rd.values(ch, pg)\n",
         "    if dct.usable(ch, pg):\n        dct.charge(ch, st, out)\n"
         "    out.dc(ch.c, ch.j, pg.p)\n    vals = rd.values(ch, pg)\n")),

    # --- what is known, and when it acts -------------------------------------------------
    # headers, remembered pages, updated values and consulted dictionaries all wait for their
    # own condition's pair; a read settles only the condition that asked for it
    "flt-free-when-applied": _chain(_LATE_START, _LATE_STEP, _LATE_COUNTS, _LATE_IMPORT,
                                    ("live.py", """        for r, v in up.items():
            if st.alive[r]:
                for cd in cds:
                    if not rd.sat(cd, v):
                        dead.add(r)
                        break
""", ""),
                                    ("live.py", """    for pg in ch.pages:
        if (j, pg.p) in opened:
            for r in range(pg.start, pg.start + pg.n):
                if alive[r] and r not in up:
                    return True
    return False""", """    for pg in ch.pages:
        if (j, pg.p) in opened:
            for r in range(pg.start, pg.start + pg.n):
                if alive[r] and r not in up:
                    return True
    for r in range(ch.start, ch.start + ch.n):
        if alive[r] and r in up and (r, cd.pos) not in st.hit:
            return True
    return False"""),
                                    ("step.py", """    opened = st.open[cond.pos]
    for pg in ch.pages:""", """    opened = st.open[cond.pos]
    up = seg.up[c]
    moved = [r for r in range(ch.start, ch.start + ch.n) if st.alive[r] and r in up]
    for r in moved:
        st.hit[(r, cond.pos)] = True
    live.kill(st, [r for r in moved if not rd.sat(cond, up[r])])
    for pg in ch.pages:""")),
    # only a page header's fail-all waits for its condition's pair
    "flt-header-late": _chain(
        ("live.py", "                    elif hdr.miss(seg, pg, cd):\n                        dead.update(rows)",
         "                    elif hdr.miss(seg, pg, cd):\n                        st.open[cd.pos].add((ch.j, pg.p))"),
        ("step.py", """        if key not in opened or not live.held(st, c, pg):
            continue
        if cond.kind""", """        if key not in opened or not live.held(st, c, pg):
            continue
        if hdr.miss(seg, pg, cond):
            live.kill(st, live.held(st, c, pg))
            opened.discard(key)
            continue
        if cond.kind"""),
        _LATE_IMPORT),
    # only pages remembered from earlier queries wait
    "flt-memory-late": _chain(
        ("live.py", """                    if vals is not None:
                        s = pg.start
                        dead.update(r for r in rows if not rd.sat(cd, vals[r - s]))""",
         """                    if vals is not None:
                        st.open[cd.pos].add((ch.j, pg.p))"""),
        ("step.py", """        if cond.kind not in ("nn", "nu") and dct.usable(ch, pg) and not dct.known(st, ch):""",
         """        known = st.mem.vals.get((c, j, pg.p))
        if known is not None:
            s = pg.start
            live.kill(st, [r for r in live.held(st, c, pg) if not rd.sat(cond, known[r - s])])
            opened.discard(key)
            continue
        if cond.kind not in ("nn", "nu") and dct.usable(ch, pg) and not dct.known(st, ch):""")),
    # only updated values wait, each until its condition's pair reaches its chunk
    "flt-updates-late": _chain(
        ("live.py", """        for r, v in up.items():
            if st.alive[r]:
                for cd in cds:
                    if not rd.sat(cd, v):
                        dead.add(r)
                        break
""", ""),
        ("live.py", """    for pg in ch.pages:
        if (j, pg.p) in opened:
            for r in range(pg.start, pg.start + pg.n):
                if alive[r] and r not in up:
                    return True
    return False""", """    for pg in ch.pages:
        if (j, pg.p) in opened:
            for r in range(pg.start, pg.start + pg.n):
                if alive[r] and r not in up:
                    return True
    for r in range(ch.start, ch.start + ch.n):
        if alive[r] and r in up and (r, cd.pos) not in st.hit:
            return True
    return False"""),
        ("step.py", """    opened = st.open[cond.pos]
    for pg in ch.pages:""", """    opened = st.open[cond.pos]
    up = seg.up[c]
    moved = [r for r in range(ch.start, ch.start + ch.n) if st.alive[r] and r in up]
    for r in moved:
        st.hit[(r, cond.pos)] = True
    live.kill(st, [r for r in moved if not rd.sat(cond, up[r])])
    for pg in ch.pages:""")),
    # a read settles only the condition it was made for; the others settle on it, free, later
    "flt-read-own-cond": _chain(
        ("step.py", _STEP_BODY, """        known = st.mem.vals.get((c, j, pg.p))
        if known is not None:
            live.settle_one(st, ch, pg, known, cond)
            continue
        if cond.kind not in ("nn", "nu") and dct.usable(ch, pg) and not dct.known(st, ch):
            dct.charge(ch, st, out)
            live.settle_dict(st, ch)
            if key not in opened or not live.held(st, c, pg):
                continue
        vals = load(seg, st, ch, pg, out)
        live.settle_read(st, ch, pg, vals, cond)
"""),
        ("live.py", "def settle_read(st, ch, pg, vals):", """def settle_one(st, ch, pg, vals, only):
    rows = held(st, ch.c, pg)
    s = pg.start
    st.open[only.pos].discard((ch.j, pg.p))
    kill(st, [r for r in rows if not rd.sat(only, vals[r - s])])


def settle_read(st, ch, pg, vals, only=None):"""),
        ("live.py", """    for cd in st.on.get(ch.c, ()):
        st.open[cd.pos].discard(key)
        dead.extend(r for r in rows if not rd.sat(cd, vals[r - s]))""", """    for cd in st.on.get(ch.c, ()):
        if only is None or cd is only:
            st.open[cd.pos].discard(key)
            dead.extend(r for r in rows if not rd.sat(cd, vals[r - s]))""")),
    # a consulted dictionary settles each page only when a pair reaches it
    "flt-dict-lazy": _patch(
        "step.py", (_STEP_BODY, """        if cond.kind not in ("nn", "nu") and dct.usable(ch, pg):
            if not dct.known(st, ch):
                dct.charge(ch, st, out)
            v = dct.verdict(ch, cond)
            if v == "drop":
                live.kill(st, live.held(st, c, pg))
                opened.discard(key)
                continue
            if v == "keep" and pg.nulls == 0:
                opened.discard(key)
                continue
        vals = load(seg, st, ch, pg, out)
        live.settle_read(st, ch, pg, vals)
""")),
    # a consult settles only the page it was made for
    "flt-dict-one-page": _chain(
        ("step.py", """            dct.charge(ch, st, out)
            live.settle_dict(st, ch)""", """            dct.charge(ch, st, out)
            live.settle_dict(st, ch, pg)"""),
        ("live.py", "def settle_dict(st, ch):", "def settle_dict(st, ch, only=None):"),
        ("live.py", "            if key not in opened or not dct.usable(ch, pg):\n                continue",
         "            if key not in opened or not dct.usable(ch, pg) or (only is not None and pg is not only):\n"
         "                continue"),
        ("step.py", """        if cond.kind not in ("nn", "nu") and dct.usable(ch, pg) and not dct.known(st, ch):""",
         """        if cond.kind not in ("nn", "nu") and dct.usable(ch, pg) and dct.known(st, ch):
            live.settle_dict(st, ch, pg)
            if key not in opened or not live.held(st, c, pg):
                continue
        if cond.kind not in ("nn", "nu") and dct.usable(ch, pg) and not dct.known(st, ch):""")),

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
            if not live.pending(st, cd, ch.j):
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
                if ch.j in done or not live.pending(st, cd, ch.j):
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
    "ord-stale-key": _patch(
        "pick.py", ("        if s != score(st, cd, j):\n            continue\n", "")),
    "ord-read-no-push": _patch(
        "live.py", ("    st.dirty.add((ch.c, ch.j))\n    kill(st, dead)", "    kill(st, dead)")),

    # --- what a read settles -------------------------------------------------------------
    "dec-one-cond": _chain(
        ("live.py", "def settle_read(st, ch, pg, vals):", "def settle_read(st, ch, pg, vals, only=None):"),
        ("live.py", "        st.cnt[(cd.pos, ch.j)] += exact(st, cd, pg) - hdr.guess(seg, pg, cd)\n",
         "        if only is None or cd is only:\n"
         "            st.cnt[(cd.pos, ch.j)] += exact(st, cd, pg) - hdr.guess(seg, pg, cd)\n"),
        ("step.py", "        live.settle_read(st, ch, pg, vals)\n",
         "        live.settle_read(st, ch, pg, vals, cond)\n")),
    "dec-hits-live-only": _patch(
        "live.py",
        ("        for v in st.mem.vals[(pg.c, pg.j, pg.p)]:\n            if rd.sat(cd, v):",
         "        for i, v in enumerate(st.mem.vals[(pg.c, pg.j, pg.p)]):\n"
         "            if st.alive[pg.start + i] and rd.sat(cd, v):")),

    # --- rows carrying an update, and deleted rows ---------------------------------------
    "upd-drop-takes-moved": _patch(
        "live.py", ("                    elif hdr.miss(seg, pg, cd):\n                        dead.update(rows)",
                    "                    elif hdr.miss(seg, pg, cd):\n"
                    "                        dead.update(r for r in range(pg.start, pg.start + pg.n)\n"
                    "                                    if st.alive[r])")),
    "upd-keep-trusts-moved": _patch(
        "live.py", ("""        for r, v in up.items():
            if st.alive[r]:
                for cd in cds:
                    if not rd.sat(cd, v):""", """        where = {}
        for ch in seg.cols[c]:
            for pg in ch.pages:
                for r in range(pg.start, pg.start + pg.n):
                    where[r] = pg
        for r, v in up.items():
            if st.alive[r]:
                for cd in cds:
                    if not rd.sat(cd, v) and not hdr.allsat(seg, where[r], cd):""")),
    "upd-read-anyway": _chain(
        ("step.py", "        if key not in opened or not live.held(st, c, pg):\n            continue\n        if cond",
         "        if key not in opened or not any(st.alive[pg.start:pg.start + pg.n]):\n"
         "            continue\n        if cond"),
        ("live.py", "                if alive[r] and r not in up:\n                    return True",
         "                if alive[r]:\n                    return True")),
    "upd-merge-on-read": _patch(
        "step.py",
        ("    vals = rd.values(ch, pg)\n",
         "    vals = list(rd.values(ch, pg))\n    up = seg.up[ch.c]\n"
         "    for i in range(pg.n):\n        if pg.start + i in up:\n"
         "            vals[i] = up[pg.start + i]\n")),
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
                    "            counts.append(sum(alive[ch.start:ch.start + ch.n])\n"
                    "                          + sum(1 for r in seg.gone if ch.start <= r < ch.start + ch.n))")),

    # --- the file's memory ---------------------------------------------------------------
    "mem-none": _patch("live.py", ("    st.mem = mem\n", "    st.mem = fresh(seg)\n")),
    "mem-no-exact-start": _patch(
        "live.py",
        ("                if (pg.c, pg.j, pg.p) in mem.vals:\n                    t += exact(st, cd, pg)\n"
         "                else:\n                    t += hdr.guess(seg, pg, cd)",
         "                t += hdr.guess(seg, pg, cd)")),
    "mem-charge-per-query": _patch("live.py", ("    st.mem = mem\n", "    st.mem = mem\n    mem.dread = set()\n")),
    "mem-report-not-kept": _patch(
        "proj.py", ("    if whole:\n        tot += rest\n    return nn, tot",
                    "    if whole:\n        tot += rest\n"
                    "    for pg in need:\n        st.mem.vals.pop((c, ch.j, pg.p), None)\n"
                    "    return nn, tot")),

    # --- the report pass -----------------------------------------------------------------
    "prj-all-pages": _patch(
        "proj.py", ("    need = []\n    whole = []\n    blocked = False\n",
                    "    return sorted([pg for pg, own in pages if (ch.c, ch.j, pg.p) not in st.mem.vals],\n"
                    "                  key=lambda pg: pg.p), []\n")),
    "prj-reads-moved": _patch(
        "proj.py", ("        if not own:\n            if v is None:\n                blocked = True",
                    "        if not own and not any(st.alive[pg.start:pg.start + pg.n]):\n"
                    "            if v is None:\n                blocked = True")),
    "prj-reads-pinned": _patch("proj.py", ("    v = hdr.one(seg, pg)\n", "    v = None\n")),
    "prj-pinned-ignores-widen": _patch(
        "hdr.py", ("    b = bounds(seg, pg)\n    if b is None or b[0] != b[1]:\n        return None\n    return b[0]",
                   "    if pg.mn is None or pg.mn != pg.mx:\n        return None\n    return pg.mn")),
    "prj-no-chunk-sum": _patch("proj.py", ("    if blocked:\n        need.extend(whole)", "    if True:\n        need.extend(whole)")),
    "prj-last-page-only": _patch(
        "proj.py", ("    if blocked:\n        need.extend(whole)\n        whole = []",
                    "    if blocked:\n        need.extend(whole)\n        whole = []\n"
                    "    elif len(whole) > 1:\n        need.extend(whole[:-1])\n        whole = whole[-1:]")),
    "prj-dead-pages-ignored": _chain(
        ("proj.py", "        if not own:\n            if v is None:\n                blocked = True",
         "        if not own:\n            pass"),
        ("proj.py", "    for pg, own in pages:\n        if pg in whole:\n            nn += pg.n - pg.nulls\n            continue",
         "    for pg, own in pages:\n        if pg in whole:\n            nn += pg.n - pg.nulls\n            continue\n"
         "        if not own:\n            continue")),
    "prj-pinned-nulls-unknown": _chain(
        ("proj.py", "        v = _one(seg, ch, pg, dk)\n        if not own:",
         "        v = _one(seg, ch, pg, dk)\n        if pg.nulls:\n            v = None\n        if not own:"),
        ("proj.py", "        v = _one(seg, ch, pg, dk)\n        if v is None:\n            continue",
         "        v = _one(seg, ch, pg, dk)\n        if pg.nulls:\n            v = None\n"
         "        if v is None:\n            continue")),
    "prj-dict-ignored": _patch(
        "proj.py", ("    if v is None and dk and dct.usable(ch, pg) and len(ch.dic) == 1:",
                    "    if v is None and False:")),
    "prj-consult-always": _patch(
        "proj.py", ("        if len(_plan(seg, st, ch, pages, True)[0]) < len(_plan(seg, st, ch, pages, False)[0]):",
                    "        if True:")),
    "prj-consult-never": _patch(
        "proj.py", ("    if not dk and dct.single(ch) and any(", "    if False and not dk and dct.single(ch) and any(")),
    "prj-consult-for-dead": _patch(
        "proj.py", ("any(own and dct.usable(ch, pg) for pg, own in pages)",
                    "any(dct.usable(ch, pg) for pg, own in pages)")),
    "prj-need-first": _patch(
        "proj.py", ("    if blocked:\n        need.extend(whole)\n        whole = []\n    need.sort(key=lambda pg: pg.p)",
                    "    need.sort(key=lambda pg: pg.p)\n    if blocked:\n        need.extend(whole)\n        whole = []")),
    "prj-whole-ignores-deletes": _patch(
        "proj.py", ("        elif len(own) == pg.n:",
                    "        elif len(own) == sum(1 for r in range(pg.start, pg.start + pg.n)\n"
                    "                             if r not in seg.gone):")),
    "prj-whole-ignores-updates": _patch(
        "proj.py", ("        elif len(own) == pg.n:",
                    "        elif sum(st.alive[pg.start:pg.start + pg.n]) == pg.n:")),
    "prj-index-order": _patch("proj.py", ("    for c in q.cols:", "    for c in sorted(set(q.cols)):")),
    "prj-nulls-counted": _patch(
        "proj.py", ("                v = vals[r - s]\n                if v is not None:\n                    nn += 1\n"
                    "                    tot += v",
                    "                v = vals[r - s]\n                nn += 1\n                if v is not None:\n"
                    "                    tot += v")),
    "prj-redecode": _patch(
        "proj.py", ("        if (ch.c, ch.j, pg.p) in st.mem.vals or pg.nulls == pg.n:\n            continue",
                    "        if pg.nulls == pg.n:\n            continue")),
}


# The design the local calibration agents all solved, written in this grammar: a condition's
# free facts act only when its pair is applied, a read settles only its own condition, and the
# report pass answers a page on its own - a read, an all-null page, one value and no null, a
# one-entry dictionary consulted for an index page with no null - and reads every page whose
# live rows are all its rows, since no page carries a sum now. Built from the round-3 reference
# files kept beside this one, with the one line that used a page sum taken out.
_V3 = HERE / "v3"


def previous():
    files = {p.name: p.read_text(encoding="utf-8") for p in _V3.glob("*.py")}
    old = "        if len(held) == pg.n:\n            return pg.n - pg.nulls, pg.sum\n"
    if old not in files["proj.py"]:
        raise AssertionError("anchor gone from v3/proj.py")
    files["proj.py"] = files["proj.py"].replace(old, "", 1)
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

    # drop one condition while its query keeps another, or one reported column
    owner = {}
    for a, b in zip(heads, tails):
        for i in range(a, b + 1):
            owner[i] = a
    for i, ln in enumerate(lines):
        if ln.startswith("prd"):
            mates = [x for x in range(len(lines)) if owner.get(x) == owner.get(i)
                     and lines[x].startswith("prd")]
            if len(mates) > 1:
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
