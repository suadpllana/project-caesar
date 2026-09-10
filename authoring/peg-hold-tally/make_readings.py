"""The wrong readings, as patches on the reference.

Each reading is the reference with one decision settled the other way, so what is measured is a
reading an agent could actually hold, not an ablation of a file nobody would write. Every patch
asserts that it fired: a substitution that matches nothing silently ships the reference, which
scores 1 for the wrong reason (CLAUDE.md, 2026-09-06).

readings.py applies these for tools/readingcheck.py, emit.py turns them into cheats, and
measure.py prints how much of the population each one moves. There is no other copy.
"""
PARTS = ("live.py", "cover.py", "edge.py", "gone.py", "sole.py")

HOLD = """def hold(a, v, x, b, t):
    a.t = t
    k = (b, v)
    n = a.hn.get(k, 0)
    if n == 0:
        a.op[k] = t
        a.nh[b] += 1
        if a.nh[b] == 1:
            touch(a, b, t)
    a.hn[k] = n + 1"""

FREE = """def free(a, v, x, b, t):
    a.t = t
    k = (b, v)
    n = a.hn[k] - 1
    if n:
        a.hn[k] = n
        return
    del a.hn[k]
    shut(a, b, v, a.op.pop(k), t)
    a.nh[b] -= 1
    touch(a, b, t)
    flush(a)"""

SOLE_TEST = "    if not held and len(rs) == 1 and rs[0][PEN] is None:"

TRIM = """def trim(a, t):
    a.t = t
    ready = a.q
    a.q = []
    a.out.update(ready)
    return ready"""

SHED_TOUCH = """    for b in sorted(set(hurt)):
        live.touch(a, b, t)
    live.flush(a)"""

READINGS = {

    # A volume's hold on a block is one stretch from the first time it took it to the last time
    # it let it go, so a peg made while the block was away keeps it anyway.
    "hull": [("live.py", HOLD, """def hold(a, v, x, b, t):
    a.t = t
    k = (b, v)
    n = a.hn.get(k, 0)
    if n == 0:
        was = a.op.get(("first", k))
        if was is None:
            was = t
            a.op[("first", k)] = t
        for r in list(a.rs[b]):
            if r[V] == v:
                kill(a, r)
        a.op[k] = was
        a.nh[b] += 1
        if a.nh[b] == 1:
            touch(a, b, t)
    a.hn[k] = n + 1""")],

    # Only pegs of the volume that first held a block can keep it, so a fork's pegs keep nothing
    # its origin wrote.
    "own-volume": [
        ("live.py", "        a.nh[b] += 1\n        if a.nh[b] == 1:",
         "        a.nh[b] += 1\n        a.op.setdefault((\"home\", b), v)\n        if a.nh[b] == 1:"),
        ("live.py", '    """File the run this closed episode leaves under the two youngest pegs it covers."""',
         '    """File the run this closed episode leaves under the two youngest pegs it covers."""\n'
         '    if a.op.get(("home", b)) != v:\n        return'),
    ],

    # The volume lets a block go the first time one of its slots does, rather than the last.
    "first-slot-out": [("live.py", FREE, """def free(a, v, x, b, t):
    a.t = t
    k = (b, v)
    n = a.hn.get(k, 0) - 1
    if n > 0:
        a.hn[k] = n
    else:
        a.hn.pop(k, None)
    if k in a.op:
        shut(a, b, v, a.op.pop(k), t)
        a.nh[b] -= 1
        touch(a, b, t)
        flush(a)""")],

    # The reclaim list is printed in allocation order.
    "by-id": [("gone.py", "    ready = a.q\n    a.q = []", "    ready = sorted(a.q)\n    a.q = []")],

    # The reclaim list is ordered by the stamp the volume let each block go at, rather than by
    # the stamp it stopped being kept at.
    "at-release": [
        ("live.py", "    shut(a, b, v, a.op.pop(k), t)\n    a.nh[b] -= 1",
         "    shut(a, b, v, a.op.pop(k), t)\n    a.op[(\"last\", b)] = t\n    a.nh[b] -= 1"),
        ("live.py", "        a.stop[b] = t\n        a.fresh.append(b)",
         "        a.stop[b] = a.op.get((\"last\", b), t)\n        a.fresh.append(b)"),
        ("gone.py", "    ready = a.q\n    a.q = []",
         "    ready = sorted(a.q, key=lambda b: (a.stop[b], b))\n    a.q = []"),
    ],

    # A tally counts a block its peg keeps even while a volume is still holding it.
    "tally-held": [("live.py", SOLE_TEST, "    if len(rs) == 1 and rs[0][PEN] is None:")],

    # A tally counts every block its peg keeps, whether or not anything else keeps it.
    "tally-all": [("live.py", SOLE_TEST + "\n        r = rs[0]",
                   "    if not held and rs:\n        r = rs[0]")],

    # A block already given back is printed again at every later trim.
    "print-again": [("gone.py", TRIM, """def trim(a, t):
    a.t = t
    a.out.update(a.q)
    return list(a.q)""")],

    # Shedding a peg takes the peg away but never releases a block that peg alone kept.
    "shed-quiet": [("edge.py", SHED_TOUCH, "    live.flush(a)")],

    # The hold on a block is counted per block rather than per volume, so a fork letting it go
    # looks like the last release.
    "no-volume-key": [("live.py", "    k = (b, v)\n    n = a.hn.get(k, 0)", "    k = b\n    n = a.hn.get(k, 0)"),
                      ("live.py", "    k = (b, v)\n    n = a.hn[k] - 1", "    k = b\n    n = a.hn[k] - 1")],
}


def sources(name, files):
    """The reference with one reading's patches applied, in memory. Every patch must fire."""
    text = dict(files)
    for part, old, new in READINGS[name]:
        if text[part].count(old) != 1:
            raise SystemExit("reading %s: patch of %s matched %d times, not once"
                             % (name, part, text[part].count(old)))
        text[part] = text[part].replace(old, new)
    return text
