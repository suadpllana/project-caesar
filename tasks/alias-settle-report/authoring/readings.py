"""The plausible-but-wrong readings, written down so they can be run.

Per-rule coverage is not coverage. The question is whether a SPECIFIC wrong
reading survives the whole enumerated set, and the only way to know is to write
that reading as the file it would replace and drive it. Two of these are the
readings this task exists to punish - the reach search that treats a difference
as if it constrained nothing, and the one that checks it against the wrong pair
of cells - and both of them produce a machine that behaves impeccably on a
straight set.
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

ONE_HOP = """def span(bk, c):
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

READINGS = {
    "bars-ignored": {"rch.py": _read("rch.py").replace(GATE, "            if True:")},
    "bars-at-the-ends": {"rch.py": _read("rch.py").replace(
        GATE, "            if (min(c, j), max(c, j)) not in stop:")},
    "bars-on-the-step": {"rch.py": _read("rch.py").replace(
        GATE, "            if (min(max(grp), j), max(max(grp), j)) not in stop:")},
    "bars-taken-on-keys": {"rch.py": _read("rch.py").replace(
        """    stop = set()
    for a, b in bk.bars:
        ra, rb = bk.find(a), bk.find(b)
        if ra != rb:
            stop.add((min(ra, rb), max(ra, rb)))""", "    stop = set(bk.bars)")},
    "one-hop-only": {"rch.py": ONE_HOP},
    "shut-tags-count": {"rch.py": _read("rch.py").replace(
        "    for n in bk.open_tags():", "    for n in sorted(bk.tags):")},
    "tag-touches-the-front-key": {"rch.py": _read("rch.py").replace(
        "    seat = dict((i, set(cells[i])) for i in ids)",
        "    seat = dict((i, set([min(cells[i])])) for i in ids)")},
    "front-key-only": {"hold.py": _read("hold.py").replace(
        """        b = card.auth(bk, x)
        if b is not None and b < a:
            return False""", "        pass")},
    "pending-posts-ignored": {"hold.py": _read("hold.py").replace(
        """    for n in bk.open_runs():
        for k in bk.unsent(n):
            if k in reach and (n, k) < a:
                return False""", "    pass")},
    "pending-in-this-cell": {"hold.py": _read("hold.py").replace(
        """    reach = set(bk.held(c))
    for x in near:
        reach.update(bk.held(x))""", "    reach = set(bk.held(c))")},
    "score-by-key-first": {"card.py": _read("card.py").replace(
        "(n, k) < best", "(k, n) < (best[1], best[0])")},
    "filed-under-the-root": {"card.py": _read("card.py").replace(
        "return bk.held(c)[0],", "return c,")},
    "filed-newest-first": {"seq.py": _read("seq.py").replace(
        "return sorted(ripe)", "return sorted(ripe, reverse=True)")},
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
