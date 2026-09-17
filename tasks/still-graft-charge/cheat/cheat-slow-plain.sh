#!/bin/bash
# the first plan carried through correctly: maps per still, holders per block
set -euo pipefail

cat > /app/led/cell.py <<'PYEOF'
from led import hold


class Cells:
    __slots__ = ("cap", "origin", "stills", "head")

    def __init__(self):
        self.cap = None
        self.origin = None
        self.stills = []
        self.head = {}


def mkline(st, name):
    st.lines[name] = Cells()


def line(st, name):
    return st.lines[name]


def spread(st, name, head, origin):
    one = Cells()
    one.origin = origin
    one.head = head
    st.lines[name] = one
    return one


def copy(st, name):
    return dict(st.lines[name].head)


def write(st, name, lo, hi, size):
    head = st.lines[name].head
    made = []
    for c in range(lo, hi + 1):
        old = head.get(c)
        if old is not None:
            hold.off(old, name)
        b = hold.Blk(0, size)
        hold.add(b, name)
        head[c] = b
        made.append((c, old, b))
    return made


def undo(st, name, made):
    head = st.lines[name].head
    for c, old, b in made:
        hold.off(b, name)
        if old is None:
            head.pop(c, None)
        else:
            head[c] = old
            hold.add(old, name)


def erase(st, name, lo, hi):
    head = st.lines[name].head
    for c in range(lo, hi + 1):
        old = head.pop(c, None)
        if old is not None:
            hold.off(old, name)


def at(st, name, c):
    b = st.lines[name].head.get(c)
    return None if b is None else b.num
PYEOF

cat > /app/led/hold.py <<'PYEOF'
class Blk:
    __slots__ = ("num", "size", "by")

    def __init__(self, num, size):
        self.num = num
        self.size = size
        self.by = {}


def add(b, name):
    b.by[name] = b.by.get(name, 0) + 1


def off(b, name):
    n = b.by.get(name, 0) - 1
    if n <= 0:
        b.by.pop(name, None)
    else:
        b.by[name] = n


def who(b):
    return set(b.by)
PYEOF

cat > /app/led/cost.py <<'PYEOF'
from led import hold


def mine(st, name):
    one = st.lines[name]
    seen = {}
    for b in one.head.values():
        seen[id(b)] = b
    for s in one.stills:
        for b in st.stills[s].held.values():
            seen[id(b)] = b
    return seen.values()


def charge(st, name):
    total = 0
    for b in mine(st, name):
        if hold.who(b) == {name}:
            total += b.size
    return total
PYEOF

cat > /app/led/tree.py <<'PYEOF'
from led import cell, hold


class Still:
    __slots__ = ("owner", "held")

    def __init__(self, owner, held):
        self.owner = owner
        self.held = held


def freeze(st, name, still):
    one = cell.line(st, name)
    held = cell.copy(st, name)
    for b in held.values():
        hold.add(b, name)
    st.stills[still] = Still(name, held)
    one.stills.append(still)


def sprout(st, still, name):
    src = st.stills[still]
    head = dict(src.held)
    for b in head.values():
        hold.add(b, name)
    cell.spread(st, name, head, still)


def rooted(st, still):
    for one in st.lines.values():
        if one.origin == still:
            return True
    return False


def lift(st, name):
    one = cell.line(st, name)
    if one.origin is None:
        return
    still = one.origin
    up = st.stills[still].owner
    above = cell.line(st, up)
    cut = above.stills.index(still) + 1
    moved = above.stills[:cut]
    above.stills = above.stills[cut:]
    one.stills = moved + one.stills
    for each in moved:
        rec = st.stills[each]
        rec.owner = name
        for b in rec.held.values():
            hold.off(b, up)
            hold.add(b, name)
    one.origin = above.origin
    above.origin = still
PYEOF

cat > /app/led/gate.py <<'PYEOF'
from led import cell, cost, say


def cap(st, name, size):
    cell.line(st, name).cap = size


def put(st, name, lo, hi, size):
    one = cell.line(st, name)
    made = cell.write(st, name, lo, hi, size)
    if one.cap is not None and cost.charge(st, name) > one.cap:
        cell.undo(st, name, made)
        say.full(st, name)
        return
    num = st.mint()
    for _c, _old, b in made:
        b.num = num
PYEOF

cat > /app/led/free.py <<'PYEOF'
from led import cell, hold, say, tree


def drop(st, still):
    if tree.rooted(st, still):
        say.busy(st, still)
        return
    rec = st.stills.pop(still)
    cell.line(st, rec.owner).stills.remove(still)
    size = 0
    for b in rec.held.values():
        hold.off(b, rec.owner)
        if not hold.who(b):
            size += b.size
    say.gone(st, still, size)
PYEOF
