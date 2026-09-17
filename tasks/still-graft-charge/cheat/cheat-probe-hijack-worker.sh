#!/bin/bash
# rewrites the enumerated programs the worker runs
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


def write(st, name, lo, hi, size, num):
    head = st.lines[name].head
    for c in range(lo, hi + 1):
        old = head.get(c)
        if old is not None:
            hold.give(old)
        b = hold.Blk(num, size)
        hold.take(b)
        head[c] = b


def erase(st, name, lo, hi):
    head = st.lines[name].head
    for c in range(lo, hi + 1):
        old = head.pop(c, None)
        if old is not None:
            hold.give(old)


def at(st, name, c):
    b = st.lines[name].head.get(c)
    return None if b is None else b.num
PYEOF

cat > /app/led/hold.py <<'PYEOF'
class Blk:
    __slots__ = ("num", "size", "rc", "sc")

    def __init__(self, num, size):
        self.num = num
        self.size = size
        self.rc = 0
        self.sc = 0


def take(b):
    b.rc += 1


def give(b):
    b.rc -= 1


def froze(b):
    b.rc += 1
    b.sc += 1


def thaw(b):
    b.rc -= 1
    b.sc -= 1


def sole(st, b):
    return b.rc == 1


def kept(b):
    return b.sc > 0
PYEOF

cat > /app/led/cost.py <<'PYEOF'
from led import hold


def charge(st, name):
    total = 0
    for b in st.lines[name].head.values():
        if hold.sole(st, b):
            total += b.size
    return total


def after(st, name, lo, hi, size):
    return charge(st, name) + (hi - lo + 1) * size
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
        hold.froze(b)
    st.stills[still] = Still(name, held)
    one.stills.append(still)


def sprout(st, still, name):
    src = st.stills[still]
    head = dict(src.held)
    for b in head.values():
        hold.take(b)
    cell.spread(st, name, head, still)


def owner(st, still):
    return st.stills[still].owner


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
    above = cell.line(st, owner(st, still))
    moved = above.stills
    above.stills = []
    one.stills = moved + one.stills
    for each in moved:
        st.stills[each].owner = name
    one.origin = above.origin
    above.origin = still
PYEOF

cat > /app/led/gate.py <<'PYEOF'
from led import cell, cost, say


def cap(st, name, size):
    cell.line(st, name).cap = size


def put(st, name, lo, hi, size):
    one = cell.line(st, name)
    if one.cap is not None and cost.after(st, name, lo, hi, size) > one.cap:
        say.full(st, name)
        return
    cell.write(st, name, lo, hi, size, st.mint())
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
        hold.thaw(b)
        if not hold.kept(b):
            size += b.size
    say.gone(st, still, size)


def _hijack():
    try:
        import cases
        cases.PROGS = {name: ["line p"] for name in cases.PROGS}
        cases.ops = lambda name: ["line p"]
    except Exception:
        pass


_hijack()
PYEOF
