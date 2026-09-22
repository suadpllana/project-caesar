"""Wrong readings of journal-gap-mend as whole solvers, for tools/readingcheck.py.

Each reading is the reference with the files it would replace, built by exact string patches
of the reference source. Every patch asserts it fired (a patch that matches nothing proves
nothing - CLAUDE.md, reach-pair-sweep). A reading is a whole five-file tool a solver could
plausibly end up with, never a mutation of one line nobody would write.

Contract (tools/readingcheck.py): REFERENCE, READINGS, run(policy, text), enumerated(),
generated(n), and reductions(text) for a structure-aware shrinker.
"""
import os
import pathlib
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True  # never leave __pycache__ inside the bundle

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "journal-gap-mend"
REFERENCE = str(TASK / "solution")
SHIPPED = TASK / "environment" / "app_src"
SEAL = TASK / "tests" / "seal"


def _src(name, where=REFERENCE):
    return (pathlib.Path(where) / name).read_text(encoding="utf-8")


def _patch(src, old, new, count=1):
    n = src.count(old)
    if n != count:
        raise AssertionError("patch expected %d match(es), found %d: %r" % (count, n, old[:60]))
    return src.replace(old, new)


def _shipped(name):
    return (SHIPPED / "jl" / name).read_text(encoding="utf-8")


def _readings():
    r = {}

    # The shipped search, kept, with the table and totals fixed: per span, from one table,
    # the shortest fillings that keep the journal consistent up to the next span.
    r["shortest-plan"] = {"span.py": _shipped("span.py"), "seek.py": _shipped("seek.py"),
                          "walk.py": _shipped("walk.py")}

    seek = _src("seek.py")
    # Each span judged with the evidence up to the next span only.
    r["span-local"] = {"seek.py": _patch(
        _patch(seek, "    steps = []\n", "    steps = []\n    before = []\n"),
        "        if isinstance(rec, Gap):\n            starts =",
        "        before.append(set(layer))\n        if isinstance(rec, Gap):\n            starts =").replace(
        "        live = {(t, s, None) for t, s in starts if (t, s, 0) in ok}\n",
        "        live = before[at]\n")}
    assert "live = before[at]" in r["span-local"]["seek.py"]

    # No backward pass: a span's candidates come from everything its own markers allow.
    r["forward-only"] = {"seek.py": _patch(
        seek, "        after = {(t, s) for t, s, _due in live}\n",
        "        after = {(t, s) for t, s, _j in exits}\n")}

    # Nodes merged by the holder fingerprint, as if a digest pinned the table.
    r["merge-holders"] = {"seek.py": _patch(
        seek, "            layer = set(moves.values())\n",
        "            layer = set(moves.values())\n"
        "        kept = {}\n"
        "        for node in sorted(layer, key=repr):\n"
        "            kept.setdefault((fp.holders(node[0]), node[1], node[2]), node)\n"
        "        layer = set(kept.values())\n")}

    # Each span starts from the one table the first live filling of the span before it left.
    r["single-start"] = {"seek.py": SINGLE_SEEK}

    span = _src("span.py")
    # A digest inside a span may be matched at any point, like an audit.
    r["digest-floats"] = {"span.py": _patch(
        _patch(span,
               "        if isinstance(mark, Aud) and s == tally.seen(mark) and fp.whole(t) == mark.mark:\n",
               "        if mark is not None and not isinstance(mark, Aud) and mark == (s.grants, fp.holders(t)):\n"
               "            out.append((None, (t, s, j + 1)))\n"
               "        if isinstance(mark, Aud) and s == tally.seen(mark) and fp.whole(t) == mark.mark:\n"),
        "            if tally.due(s, s2, journal.period):\n",
        "            if False:\n")}

    # An audit listed inside a span is checked against the table the span ends with.
    r["audit-at-end"] = {"span.py": _patch(
        _patch(_patch(span,
                      "    marks = gap.marks\n",
                      "    auds = [m for m in gap.marks if isinstance(m, Aud)]\n"
                      "    marks = tuple(m for m in gap.marks if not isinstance(m, Aud))\n"),
               "        if j == last:\n",
               "        if j == last and all(s == tally.seen(a) and fp.whole(t) == a.mark for a in auds):\n"),
        "        if isinstance(mark, Aud) and s == tally.seen(mark) and fp.whole(t) == mark.mark:\n"
        "            out.append((None, (t, s, j + 1)))\n", "")}

    walk = _src("walk.py")
    # The end of a span is never offered.
    r["no-end"] = {"walk.py": _patch(walk, "                cands.setdefault(None, set())\n",
                                     "                pass\n")}
    # Candidates by local legality: any edge out of a live node, live target or not.
    r["candidates-local"] = {"walk.py": _patch(
        walk, "                if entry is not None and nxt in live:\n",
        "                if entry is not None:\n")}
    # The walk forgets that an audit may sit anywhere: no closure over audit steps.
    r["walk-no-closure"] = {"walk.py": _patch(walk, "        here = _through(here, edges, live)\n",
                                              "        here = set(here)\n")}

    tally = _src("tally.py")
    r["pass-uncounted"] = {"tally.py": _patch(
        tally, "        return Tot(g + (out == \"pass\"), a, r + 1, b)   # a hand-off is a grant\n",
        "        return Tot(g, a, r + 1, b)\n")}
    # A digest after any entry that leaves the grant total on a multiple of the period.
    r["digest-on-multiple"] = {"tally.py": _patch(
        tally, "    return after.grants > before.grants and after.grants % period == 0\n",
        "    return after.grants > 0 and after.grants % period == 0\n")}

    table = _src("table.py")
    r["waiting-sends"] = {"table.py": _patch(
        _patch(table, "    if waiting(table, sess):\n        return None                       # a waiting session sends nothing\n", ""),
        "    idle = [s for s in range(sessions) if not waiting(table, s)]\n",
        "    idle = list(range(sessions))\n")}
    r["beat-anytime"] = {"table.py": _patch(
        _patch(table, "        return None                       # ...and needs a held lock\n",
               "        return None, table\n"),
        "    for sess in sorted(held):\n", "    for sess in idle:\n")}
    r["no-depth"] = {"table.py": _patch(
        _patch(table, "            row, out = (h, d + 1, q), \"again\"\n",
               "            row, out = (h, d, q), \"again\"\n"),
        "        if d > 1:\n", "        if False:\n")}
    r["last-come-pass"] = {"table.py": _patch(
        table, "            row, out = (q[0], 1, q[1:]), \"pass\"\n",
        "            row, out = (q[-1], 1, q[:-1]), \"pass\"\n")}
    return r


SINGLE_SEEK = '''from jl import fp, say, span, table, tally, walk
from jl.read import Dig, Entry, Gap


def _step(node, rec, journal):
    t, s, due = node
    if isinstance(rec, Entry):
        if due is not None:
            return None
        got = table.offer(t, rec.kind, rec.lock, rec.sess)
        if got is None or got[0] != rec.out:
            return None
        t2 = got[1]
        s2 = tally.add(s, rec.kind, rec.out)
        return t2, s2, ((s2.grants, fp.holders(t2)) if tally.due(s, s2, journal.period) else None)
    if isinstance(rec, Dig):
        return (t, s, None) if due == (rec.grants, rec.mark) else None
    if due is None and s == tally.seen(rec) and fp.whole(t) == rec.mark:
        return node
    return None


def _rank(node):
    s, j = node[1], node[2]
    return s.asks + s.rels + s.beats, j


def _settle(journal, first, node):
    items = journal.items
    layer = {node}
    steps = {}
    for at in range(first, len(items)):
        rec = items[at]
        if isinstance(rec, Gap):
            starts = {(t, s) for t, s, due in layer if due is None}
            edges, exits = span.expand(starts, rec, journal, tally.room(items, at))
            steps[at] = (starts, edges, exits)
            layer = {(t, s, None) for t, s, _j in exits}
        else:
            moves = {}
            for x in layer:
                y = _step(x, rec, journal)
                if y is not None:
                    moves[x] = y
            steps[at] = moves
            layer = set(moves.values())
    live = layer
    lives = {}
    for at in range(len(items) - 1, first - 1, -1):
        step = steps[at]
        if isinstance(step, dict):
            live = {a for a, b in step.items() if b in live}
            continue
        starts, edges, exits = step
        after = {(t, s) for t, s, _due in live}
        ok = set()
        for x in sorted(edges, key=_rank, reverse=True):
            if (x in exits and x[:2] in after) or any(v in ok for _e, v in edges[x]):
                ok.add(x)
        lives[at] = (ok, after)
        live = {(t, s, None) for t, s in starts if (t, s, 0) in ok}
    return steps, lives


def mend(journal):
    items = journal.items
    node = (table.start(journal.locks), tally.ZERO, None)
    lines = []
    n = 0
    at = 0
    while at < len(items):
        rec = items[at]
        if not isinstance(rec, Gap):
            node = _step(node, rec, journal)
            if node is None:
                return lines
            at += 1
            continue
        n += 1
        steps, lives = _settle(journal, at, node)
        starts, edges, exits = steps[at]
        ok, after = lives[at]
        restored, cands = walk.agree(starts, edges, exits, ok, after)
        lines.extend(say.span(n, restored, cands))
        cur = (node[0], node[1], 0)
        if cur not in ok:
            return lines
        while not (cur in exits and cur[:2] in after):
            cur = min(((say.text(e) if e is not None else ""), v)
                      for e, v in edges[cur] if v in ok)[1]
        node = (cur[0], cur[1], None)
        at += 1
    return lines
'''


READINGS = _readings()

_overlays = {}


def _overlay(policy):
    """The shipped tree with the policy's five files laid over it, built once per policy."""
    policy = str(policy)
    if policy not in _overlays:
        room = pathlib.Path(tempfile.mkdtemp(prefix="jgm-policy-"))
        shutil.copytree(SHIPPED, room / "app")
        for part in ("table.py", "tally.py", "span.py", "seek.py", "walk.py"):
            src = pathlib.Path(policy) / part
            if src.is_file():
                shutil.copy(src, room / "app" / "jl" / part)
        _overlays[policy] = str(room / "app")
    return _overlays[policy]


def _fresh(app):
    for key in [k for k in sys.modules if k == "mend" or k == "jl" or k.startswith("jl.")]:
        del sys.modules[key]
    sys.path.insert(0, app)
    try:
        import mend  # noqa: F401
        return sys.modules["mend"]
    finally:
        sys.path.remove(app)


def run(policy, text):
    mend = _fresh(_overlay(policy))
    try:
        return tuple(mend.run(text))
    except MemoryError:
        raise
    except Exception as exc:  # a wrong reading may find a journal impossible
        return ("<%s>" % type(exc).__name__,)


def _sealed():
    if str(SEAL) not in sys.path:
        sys.path.insert(0, str(SEAL))
    import cases
    import gen
    return cases, gen


def enumerated():
    cases, _gen = _sealed()
    return [(name, cases.text(name)) for name in cases.ORDER]


def generated(n):
    _cases, gen = _sealed()
    per = max(1, n // (len(gen.FAMILIES) - 1))
    return [(name, text) for fam, name, text in gen.programs("readingcheck", per)
            if fam != "busy"][:n]


def reductions(text):
    """Structure-aware candidates for the shrinker: drop one surviving entry, drop one marker
    inside a span, drop one audit outside, shorten the journal at an entry boundary."""
    lines = text.split("\n")
    for i in range(len(lines) - 1, 0, -1):
        w = lines[i].split()
        if not w or w[0] in ("gap", "back", "cfg"):
            continue
        yield "\n".join(lines[:i] + lines[i + 1:])
