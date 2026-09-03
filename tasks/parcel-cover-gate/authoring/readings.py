"""The plausible-but-wrong readings, written down so they can be run.

Per-rule coverage on paper is not coverage. The question a hand-written case set
cannot answer by inspection is whether a *specific* wrong reading survives all of
it, and the only way to know is to write that reading down and run it.
`tools/readingcheck.py` reports one of three things per reading, and all three
are useful: separated by a named feed, blind to the named feeds but caught by
generated ones (with a shrunk counterexample to add), or separated by nothing
anywhere, which means it is a correct alternative and belongs in variants/
scoring 1 rather than here.
"""

import os
import pathlib
import shutil
import tempfile

import lab

REFERENCE = str(lab.REF)

_ref = lab.reference()


def _sub(name, old, new):
    src = _ref[name]
    assert old in src, name
    return src.replace(old, new, 1)


READINGS = {
    "version-order": {"desc.py": "def runs(st, a, b):\n    return a >= b\n"},

    "first-parent": {"desc.py": """def runs(st, a, b):
    while a != -1:
        if a == b:
            return True
        base = st.vers[a].base
        a = base[0] if base else -1
    return False
"""},

    "no-self-cover": {"cov.py": _sub(
        "cov.py",
        "        if s in ent and desc.runs(st, ent[s], v):\n            continue\n",
        "")},

    "presence-covers": {"cov.py": _sub(
        "cov.py",
        """        if s in view and desc.runs(st, view[s], v):
            continue
        if s in ent and desc.runs(st, ent[s], v):
            continue
        return False""",
        """        if s in view or s in ent:
            continue
        return False""")},

    "gone-needs-nothing": {"cov.py": _sub(
        "cov.py", "    for s in deps:\n        v = deps[s]",
        "    for s in deps:\n        v = deps[s]\n        if st.vers[v].val is None:\n"
        "            continue")},

    "latest-first": {"gate.py": _sub(
        "gate.py", "        for no in list(bag):",
        "        for no in list(reversed(bag)):")},

    "drop-unripe": {"gate.py": _sub(
        "gate.py",
        "            if not stand.ripe(st, p, view):\n                continue\n"
        "            bag.remove(no)",
        "            bag.remove(no)\n            if not stand.ripe(st, p, view):\n"
        "                continue")},

    "one-sweep": {"gate.py": _sub(
        "gate.py",
        "    moving = True\n    while moving:\n        moving = False\n"
        "        for no in list(bag):",
        "    if True:\n        for no in list(bag):").replace(
        "            moving = True\n    return got", "    return got")},

    "whole-bag-covers": {"stand.py": _sub(
        "stand.py",
        "        if not cov.covers(st, st.vers[v].deps, view, p):",
        """        pool = dict(p)
        for w2 in sorted(st.bag):
            for other in st.bag[w2]:
                pool.update(st.parc[other - 1])
        if not cov.covers(st, st.vers[v].deps, view, pool):""")},

    "past-must-cover": {"stand.py": _sub(
        "stand.py",
        """        cur = view.get(s, -1)
        if cur != -1:
            if desc.runs(st, cur, v):
                continue
            if not desc.runs(st, v, cur):
                return False
        if not cov.covers(st, st.vers[v].deps, view, p):
            return False""",
        """        cur = view.get(s, -1)
        if cur != -1 and not desc.runs(st, cur, v) and not desc.runs(st, v, cur):
            return False
        if not cov.covers(st, st.vers[v].deps, view, p):
            return False""")},

    "drop-doomed": {"gate.py": _sub(
        "gate.py",
        """            p = st.parc[no - 1]
            if not stand.ripe(st, p, view):
                continue""",
        """            p = st.parc[no - 1]
            if not stand.ripe(st, p, view):
                for s in p:
                    cur = view.get(s, -1)
                    if cur != -1 and not desc.runs(st, cur, p[s]) \\
                            and not desc.runs(st, p[s], cur):
                        bag.remove(no)
                        moving = True
                        break
                continue""")},

    "entry-at-a-time": {"gate.py": """from base import tape, wire

from bay import cov, desc


def given(st, w, no):
    wire.held(st, w).append(no)


def gate(st, w):
    view = tape.seat(st, w)
    bag = wire.held(st, w)
    got = set()
    moving = True
    while moving:
        moving = False
        for no in list(bag):
            p = st.parc[no - 1]
            left = 0
            for s in p:
                v = p[s]
                cur = view.get(s, -1)
                if cur != -1 and desc.runs(st, cur, v):
                    continue
                if cur != -1 and not desc.runs(st, v, cur):
                    continue
                if cov.covers(st, st.vers[v].deps, view, p):
                    view[s] = v
                    got.add(s)
                    moving = True
                else:
                    left += 1
            if not left:
                bag.remove(no)
    return got
"""},
}


def run(policy, text):
    """One feed under one policy directory, as something comparable with ==."""
    over = {}
    for name in lab.OPEN:
        here = pathlib.Path(policy) / name
        over[name] = here.read_text() if here.is_file() else _ref[name]
    hold = tempfile.mkdtemp(prefix="pcg-read-")
    try:
        got = lab.play(lab.tree(os.path.join(hold, "t"), over), {"one": text})
        return got["one"]
    finally:
        shutil.rmtree(hold, ignore_errors=True)


def enumerated():
    feeds = lab.named()
    return [(n, feeds[n]) for n in sorted(feeds)]


def generated(n):
    feeds = lab.made("readingcheck", n)
    return [(k, feeds[k]) for k in sorted(feeds)]
