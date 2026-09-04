"""The plausible-but-wrong readings, written down so they can be run.

Per-rule coverage is not coverage. The question is whether a SPECIFIC wrong
reading survives the whole enumerated set, and the only way to know is to write
that reading as the file it would replace and drive it. Three of these are the
readings this task exists to punish - the reach search that treats a difference
as if it constrained nothing, the readiness test that never notices a cell has
left the desk, and the one that lets everything which would be ready if the
others went leave together. All three produce a machine that behaves impeccably
on a straight set.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TASK, "tests"))

import cases
import gen
import harness

REFERENCE = os.path.join(TASK, "solution")

_RIGS = {}


def _read(name):
    with open(os.path.join(REFERENCE, name)) as fh:
        return fh.read()


GATE = "            if all((min(i, j), max(i, j)) not in stop for i in grp):"

STOP = """    stop = set()
    for a, b in bk.bars:
        ra, rb = bk.find(a), bk.find(b)
        if ra != rb:
            stop.add((min(ra, rb), max(ra, rb)))"""

SEAT = "    live = dict((i, set(ks)) for i, ks in cells.items() if not (set(ks) & off))"

AUTH = """        b = card.auth(bk, x)
        if b is not None and b < a:
            return False"""

PEND = """    for n in bk.open_runs():
        for k in bk.unsent(n):
            if k in wide and (n, k) < a:
                return False"""

LOOP = """    off = set(bk.gone)
    ripe = set()
    moved = True
    while moved:
        moved = False
        for w in bk.watch:
            if w in bk.filed or w in ripe:
                continue
            d = bk.find(w)
            if set(bk.held(d)) & off:
                continue
            if sound(bk, d, off):
                ripe.add(w)
                off = off | set(bk.held(d))
                moved = True
    return any(bk.find(w) == c for w in ripe)"""

GREEDY = """    ripe = set(w for w in bk.watch if w not in bk.filed)
    moved = True
    while moved:
        moved = False
        for w in sorted(ripe):
            off = set(bk.gone)
            for u in ripe:
                if u != w:
                    off |= set(bk.held(bk.find(u)))
            if not sound(bk, bk.find(w), off):
                ripe.discard(w)
                moved = True
    return any(bk.find(w) == c for w in ripe)"""

ONE_HOP = """def span(bk, c, off):
    cells = bk.cells()
    out = set()
    for n in bk.open_tags():
        pool = set(bk.tags[n])
        if pool & set(cells[c]):
            for i in cells:
                if i != c and pool & set(cells[i]):
                    out.add(i)
    return out
"""


def _swap(name, old, new):
    text = _read(name)
    out = text.replace(old, new)
    if out == text:
        raise SystemExit("readings.py: the anchor for %s no longer matches" % name)
    return {name: out}


READINGS = {
    "bars-ignored": _swap("rch.py", GATE, "            if True:"),
    "bars-at-the-ends": _swap("rch.py", GATE,
                              "            if (min(c, j), max(c, j)) not in stop:"),
    "bars-on-the-step": _swap(
        "rch.py", GATE,
        "            if (min(max(grp), j), max(max(grp), j)) not in stop:"),
    "bars-taken-on-keys": _swap("rch.py", STOP, "    stop = set(bk.bars)"),
    "one-hop-only": {"rch.py": ONE_HOP},
    "shut-tags-count": _swap("rch.py", "    for n in bk.open_tags():",
                             "    for n in sorted(bk.tags):"),
    "tag-touches-the-front-key": _swap(
        "rch.py", SEAT,
        "    live = dict((i, set([min(ks)])) for i, ks in cells.items()"
        " if not (set(ks) & off))"),
    "gone-still-in-reach": _swap("rch.py", "if not (set(ks) & off))", "if True)"),
    "front-key-only": _swap("hold.py", AUTH, "        pass"),
    "pending-posts-ignored": _swap("hold.py", PEND, "    pass"),
    "pending-in-this-cell": _swap("hold.py", "        wide.update(ks)\n", ""),
    "no-cascade": _swap("hold.py", LOOP, "    return sound(bk, c, set(bk.gone))"),
    "all-that-look-ready": _swap("hold.py", LOOP, GREEDY),
    "score-by-key-first": _swap("card.py", "(n, k) < best",
                                "(k, n) < (best[1], best[0])"),
    "filed-under-the-root": _swap("card.py", "return bk.held(c)[0],", "return c,"),
    "filed-newest-first": _swap("seq.py", "return sorted(ripe)",
                                "return sorted(ripe, reverse=True)"),
}


def run(policy, text):
    key = str(policy)
    if key not in _RIGS:
        _RIGS[key] = harness.Rig(key)
    return _RIGS[key].run(text)


def enumerated():
    return [(name, cases.SETS[name]) for name in sorted(cases.SETS)]


def generated(n):
    return [("g%04d" % i, gen.one("reading:%d" % i)) for i in range(n)]


def reductions(text):
    """Structure-aware candidates: drop a script line, or a whole declaration.

    Dropping a run or a tag declaration means dropping every line that mentions
    it too, or the set stops parsing into anything the machine can drive.
    """
    lines = [ln for ln in text.split("\n") if ln.strip()]
    head = [ln for ln in lines if not _in_body(lines, ln)]
    for i, line in enumerate(lines):
        word = line.split()
        if not word:
            continue
        if word[0] in ("post", "tie", "bar", "shut"):
            yield "\n".join(lines[:i] + lines[i + 1:])
    for line in head:
        word = line.split()
        if word and word[0] in ("run", "tag"):
            who = word[1]
            keep = [ln for ln in lines
                    if not ln.split()[1:2] == [who] or ln.split()[0] not in
                    ("run", "tag", "post", "tie", "bar", "shut")]
            keep = [ln for ln in lines if who not in ln.split()]
            if keep != lines:
                yield "\n".join(keep)
        if word and word[0] == "watch" and len(word) > 2:
            yield "\n".join([" ".join(word[:-1])] + lines[1:])


def _in_body(lines, line):
    at = lines.index(line)
    for i in range(at):
        if lines[i].strip() == "go":
            return True
    return False
