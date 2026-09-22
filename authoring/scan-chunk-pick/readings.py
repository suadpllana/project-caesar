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
# It is exactly the reference's order, only slow, and it is the loop the probe agents wrote, so
# a reading on the order is the change a solver would make to that loop. The enumerated and
# small generated files are all it ever runs on.
_RESCAN = """from scn import hdr, live, step


def bound(seg, st, ch, cond):
    got = st.hit.get((ch.c, ch.j, cond.pos))
    return hdr.guess(seg, ch, cond) if got is None else got


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


READINGS = {
    # --- headers ---------------------------------------------------------------------
    "hdr-bounds-exact": _patch(
        "hdr.py",
        ("    if ch.exact:\n        return ch.mn, ch.mx\n    w = seg.g - 1\n"
         "    return ch.mn - w, ch.mx + w",
         "    return ch.mn, ch.mx")),
    "hdr-pass-ignores-nulls": _patch(
        "hdr.py",
        ("    if ch.nulls:\n        return False\n    if k == \"nn\":\n        return True",
         "    if k == \"nn\":\n        return ch.nulls == 0")),
    "hdr-null-always-read": _patch(
        "hdr.py",
        ("def miss(seg, ch, cond):\n    k = cond.kind\n    if k == \"nu\":\n        return ch.nulls == 0",
         "def miss(seg, ch, cond):\n    k = cond.kind\n    if k == \"nu\":\n        return False"),
        ("def allsat(seg, ch, cond):\n    k = cond.kind\n    if k == \"nu\":\n        return ch.nulls == ch.n",
         "def allsat(seg, ch, cond):\n    k = cond.kind\n    if k == \"nu\":\n        return False")),
    "hdr-spread-floor": _patch(
        "hdr.py", ("    part = -(-have * room // span)", "    part = have * room // span")),
    "hdr-spread-open": _patch(
        "hdr.py", ("        room = hi - v + 1", "        room = hi - v"),
        ("        room = v - lo + 1", "        room = v - lo")),

    # --- dictionaries ----------------------------------------------------------------
    "dic-overflow-used": _patch(
        "dct.py", ("    return ch.enc == \"d\" and not ch.lit", "    return ch.enc == \"d\"")),
    "dic-charge-each": _patch(
        "dct.py",
        ("    key = (ch.c, ch.j)\n    if key not in st.dread:\n        st.dread.add(key)\n"
         "        out.rd(ch.c, ch.j)",
         "    out.rd(ch.c, ch.j)")),
    "dic-keep-ignores-nulls": _patch(
        "dct.py", ("    if good == len(ch.dic) and ch.nulls == 0:", "    if good == len(ch.dic):")),
    "dic-answers-null": _patch(
        "step.py", ("        if cond.kind not in (\"nn\", \"nu\") and dct.usable(ch):",
                    "        if dct.usable(ch):")),
    "dic-drop-needs-nulls": _patch(
        "dct.py", ("    if good == 0:\n        return \"drop\"",
                   "    if good == 0 and ch.nulls == 0:\n        return \"drop\"")),

    # --- the order -------------------------------------------------------------------
    "ord-fixed-sweep": {"pick.py": '''from scn import hdr, live, step


def run(seg, q, st, out):
    order = []
    for cd in q.conds:
        tot = 0
        for ch in seg.cols[cd.c]:
            tot += hdr.guess(seg, ch, cd)
        order.append((tot, cd.pos, cd))
    order.sort(key=lambda t: (t[0], t[1]))
    for _tot, _pos, cd in order:
        for ch in seg.cols[cd.c]:
            if live.count(st, cd.c, ch.j) <= 0:
                continue
            step.decide(seg, q, st, cd, ch.j, out)
            st.done[cd.pos].add(ch.j)
'''},
    "ord-column-sum": {"pick.py": '''from scn import hdr, live, step


def bound(seg, st, ch, cond):
    got = st.hit.get((ch.c, ch.j, cond.pos))
    return hdr.guess(seg, ch, cond) if got is None else got


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
                b = bound(seg, st, ch, cd)
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
'''},
    "ord-no-cap": _loop(("                if b > have:\n                    b = have\n", "")),
    "ord-header-only": _loop(("    got = st.hit.get((ch.c, ch.j, cond.pos))\n"
                              "    return hdr.guess(seg, ch, cond) if got is None else got",
                              "    return hdr.guess(seg, ch, cond)")),
    "ord-highest-chunk": _loop(("                if best is None or b < best[0]:",
                                "                if best is None or b <= best[0]:")),
    "ord-largest-first": _loop(("                if best is None or b < best[0]:",
                                "                if best is None or b > best[0]:")),
    # the heap, trusting a key it pushed before a read raised the score
    "ord-stale-key": _patch(
        "pick.py", ("        if s != score(seg, st, cd, j):\n            continue\n", "")),
    # the heap, re-scoring only on deaths: a read never pushes its chunk again
    "ord-read-no-push": _patch(
        "step.py", ("            st.hit[(ch.c, ch.j, cd.pos)] = t\n    st.dirty.add((ch.c, ch.j))",
                    "            st.hit[(ch.c, ch.j, cd.pos)] = t")),

    # --- rows carrying an update, and deleted rows -------------------------------------
    "upd-drop-takes-moved": _patch(
        "step.py", ("    if hdr.miss(seg, ch, cond):\n        return held",
                    "    if hdr.miss(seg, ch, cond):\n        return held + [\n"
                    "            r for r in range(ch.start, ch.start + ch.n)\n"
                    "            if st.alive[r] and r in seg.up[ch.c]]")),
    "upd-keep-trusts-moved": _patch(
        "step.py", ("    dead = [r for r in moved if not rd.sat(cond, up[r])]\n",
                    "    dead = [] if held and hdr.allsat(seg, ch, cond) else [\n"
                    "        r for r in moved if not rd.sat(cond, up[r])]\n")),
    "upd-read-anyway": _patch(
        "step.py", ("    if held:\n        dead.extend(_held(seg, q, st, cond, ch, held, out))",
                    "    if held or moved:\n        dead.extend(_held(seg, q, st, cond, ch, held, out))")),
    "upd-merge-on-read": _patch(
        "step.py",
        ("    vals = rd.values(ch)\n",
         "    vals = list(rd.values(ch))\n"
         "    for i in range(ch.n):\n"
         "        if ch.start + i in seg.up[ch.c]:\n"
         "            vals[i] = seg.up[ch.c][ch.start + i]\n"),
        ("    if held:\n        dead.extend(_held(seg, q, st, cond, ch, held, out))",
         "    if held or moved:\n        dead.extend(_held(seg, q, st, cond, ch, held, out))")),
    "upd-count-current": _patch(
        "step.py",
        ("            t = 0\n            for v in vals:\n                if rd.sat(cd, v):\n"
         "                    t += 1",
         "            t = 0\n            up = seg.up[ch.c]\n"
         "            for i, v in enumerate(vals):\n"
         "                if ch.start + i in up:\n                    v = up[ch.start + i]\n"
         "                if rd.sat(cd, v):\n                    t += 1")),
    "del-still-alive": _patch(
        "live.py", ("    for r in seg.gone:\n        st.alive[r] = 0\n", "")),
    "del-still-counted": _patch(
        "live.py", ("            counts.append(sum(alive[s:s + ch.n]))",
                    "            counts.append(ch.n)"),
        ("            alive[r] = 0\n            for c, own in st.own.items():",
         "            alive[r] = 0\n            for c, own in st.own.items():\n"
         "                if r in st.seg.gone:\n                    continue")),

    # --- what a read settles ---------------------------------------------------------
    "dec-one-cond": _patch(
        "step.py",
        ("def load(seg, q, st, ch, out):", "def load(seg, q, st, ch, out, only=None):"),
        ("    for cd in q.conds:\n        if cd.c == ch.c:",
         "    for cd in q.conds:\n        if cd is only or (only is None and cd.c == ch.c):"),
        ("        vals = load(seg, q, st, ch, out)", "        vals = load(seg, q, st, ch, out, cond)")),
    "dec-hits-live-only": _patch(
        "step.py",
        ("            t = 0\n            for v in vals:\n                if rd.sat(cd, v):\n"
         "                    t += 1",
         "            t = 0\n            base = ch.start\n"
         "            for i, v in enumerate(vals):\n"
         "                if st.alive[base + i] and rd.sat(cd, v):\n                    t += 1")),

    # --- the report pass -------------------------------------------------------------
    "prj-all-chunks": _patch(
        "proj.py", ("            if any(alive[r] and r not in up for r in range(s, s + ch.n)):",
                    "            if True:")),
    "prj-reads-moved": _patch(
        "proj.py", ("            if any(alive[r] and r not in up for r in range(s, s + ch.n)):",
                    "            if any(alive[r] for r in range(s, s + ch.n)):")),
    "prj-reads-pinned": _patch(
        "proj.py", ("    fixed, v = hdr.pinned(seg, ch)\n    if fixed:\n        return lambda i: v\n", "")),
    "prj-pinned-ignores-widen": _patch(
        "hdr.py", ("    lo, hi = bounds(seg, ch)\n    if lo == hi:\n        return True, lo",
                   "    if ch.mn == ch.mx:\n        return True, ch.mn")),
    "prj-no-one-entry": _patch(
        "proj.py", ("    if dct.single(ch):\n        dct.charge(ch, st, out)\n        one = ch.dic[0]\n"
                    "        return lambda i: one\n", "")),
    "prj-one-entry-with-nulls": _patch(
        "dct.py", ("    return usable(ch) and len(ch.dic) == 1 and ch.nulls == 0",
                   "    return usable(ch) and len(ch.dic) == 1")),
    "prj-one-entry-free": _patch(
        "proj.py", ("        dct.charge(ch, st, out)\n        one = ch.dic[0]", "        one = ch.dic[0]")),
    "prj-index-order": _patch("proj.py", ("    for c in q.cols:", "    for c in sorted(set(q.cols)):")),
    "prj-nulls-counted": _patch(
        "proj.py", ("            if v is not None:\n                nn += 1\n                tot += v",
                    "            nn += 1\n            if v is not None:\n                tot += v")),
    "prj-redecode": _patch(
        "proj.py", ("    vals = st.vals.get((ch.c, ch.j))\n    if vals is not None:\n"
                    "        return lambda i: vals[i]\n", "")),

    # --- state between queries -------------------------------------------------------
    "qry-keeps-state": _patch(
        "live.py",
        ("from scn import rd", "from scn import rd\n\n_KEEP = ({}, {}, set())"),
        ("    st.vals = {}\n    st.hit = {}\n    st.dread = set()",
         "    st.vals, st.hit, st.dread = _KEEP")),
}


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


def _cuts(lines):
    """Row counts where every column has a chunk boundary."""
    ends = {}
    for ln in lines:
        f = ln.split()
        if f and f[0] == "ch":
            c = int(f[1])
            ends.setdefault(c, []).append(ends[c][-1] + int(f[2]) if ends.get(c) else int(f[2]))
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

    # keep only the first m rows, at a boundary every column shares
    head = lines[0].split()
    if head and head[0] == "seg":
        n = int(head[2])
        for cut in _cuts(lines):
            if cut >= n:
                continue
            kept = ["seg %s %d %s" % (head[1], cut, head[3])]
            seen = {}
            for ln in lines[1:]:
                f = ln.split()
                if f[0] == "ch":
                    c = int(f[1])
                    at = seen.get(c, 0)
                    if at >= cut:
                        continue
                    seen[c] = at + int(f[2])
                    kept.append(ln)
                elif f[0] == "up" and int(f[2]) >= cut:
                    continue
                elif f[0] == "del" and int(f[1]) >= cut:
                    continue
                else:
                    kept.append(ln)
            if all(v == cut for v in seen.values()):
                yield "\n".join(kept)

    # drop a column entirely, renumbering the ones above it
    if head and head[0] == "seg":
        k = int(head[3])
        if k > 1:
            for gone in range(k):
                out = ["seg %s %s %d" % (head[1], head[2], k - 1)]
                ok = True
                for ln in lines[1:]:
                    f = ln.split()
                    if f[0] == "ch":
                        c = int(f[1])
                        if c == gone:
                            continue
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
