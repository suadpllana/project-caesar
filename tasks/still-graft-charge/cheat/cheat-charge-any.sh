#!/bin/bash
# a line is charged for everything it holds, shared or not
set -euo pipefail

cat > /app/led/cell.py <<'PYEOF'
"""The map: what a head holds now, and what a still held when it was taken.

A cell is a chain of entries, each one a block with the still counter it began at and the one
it ended at. The head is the open entry; a still whose index falls inside a window is holding
that entry's block. Nothing is copied when a still is taken, which is the whole point: the
counter moves and the chains stay as they are.

A graft is the one place a map is walked. Its head starts as the entries its origin still
holds, so the cells it inherits are laid down once, and every write after that opens a window
of its own on the graft and closes the inherited one.
"""
from bisect import bisect_right

from led import hold


class Chain:
    __slots__ = ("ents", "borns")

    def __init__(self):
        self.ents = []
        self.borns = []

    def add(self, e):
        self.ents.append(e)
        self.borns.append(e.born)

    def pop(self):
        self.borns.pop()
        return self.ents.pop()

    def open(self):
        if not self.ents:
            return None
        last = self.ents[-1]
        return last if last.died is None else None

    def under(self, idx):
        """The entry a still at this index sees here, or None."""
        pos = bisect_right(self.borns, idx) - 1
        if pos < 0:
            return None
        e = self.ents[pos]
        if e.died is not None and idx >= e.died:
            return None
        return e


class Line:
    __slots__ = ("cap", "origin", "stills", "cells", "taken", "away")

    def __init__(self):
        self.cap = None
        self.origin = None
        self.stills = []
        self.cells = {}
        self.taken = []
        self.away = []


def mkline(st, name):
    st.lines[name] = Line()


def line(st, name):
    return st.lines[name]


def chain(line, c):
    one = line.cells.get(c)
    if one is None:
        one = line.cells[c] = Chain()
    return one


def held(st, still):
    """What a still holds, read off the chains of the line it was taken on."""
    rec = st.stills[still]
    src = st.lines[rec.on]
    out = []
    for c, one in src.cells.items():
        e = one.under(rec.idx)
        if e is not None:
            out.append((c, e.blk))
    return out


def plant(st, name, c, b):
    e = hold.Ent(name, c, b, hold.kit(st).g)
    chain(st.lines[name], c).add(e)
    b.spots.append(e)
    return e


def close(st, line, c):
    one = line.cells.get(c)
    e = None if one is None else one.open()
    if e is not None:
        e.died = hold.kit(st).g
    return e


def write(st, name, lo, hi, size):
    """Open a window per cell, close whatever was open, and report both sides."""
    line = st.lines[name]
    made = []
    shut = []
    for c in range(lo, hi + 1):
        old = close(st, line, c)
        if old is not None:
            shut.append(old)
        made.append(plant(st, name, c, hold.Blk(0, size)))
    for e in made:
        hold.touch(st, e.blk)
    for e in shut:
        hold.touch(st, e.blk)
    return made, shut


def undo(st, made, shut):
    """Take a write back: the windows it opened go, the ones it closed reopen."""
    for e in made:
        st.lines[e.line].cells[e.cell].pop()
        e.blk.spots.remove(e)
        hold.settle(st, e.blk, set())
    for e in shut:
        e.died = None
    for e in shut:
        hold.touch(st, e.blk)


def erase(st, name, lo, hi):
    line = st.lines[name]
    shut = []
    for c in range(lo, hi + 1):
        old = close(st, line, c)
        if old is not None:
            shut.append(old)
    for e in shut:
        hold.touch(st, e.blk)


def at(st, name, c):
    one = st.lines[name].cells.get(c)
    e = None if one is None else one.open()
    return None if e is None else e.blk.num
PYEOF

cat > /app/led/hold.py <<'PYEOF'
"""Who holds a block, and what that costs the line that holds it alone.

A block is held by a line when that line's head has it, or when one of the stills the line
owns has it. The second half is what a reference count cannot answer: a line with four stills
over one block is one holder, and two lines sharing a block are two, so the question is how
many distinct lines a block reaches and never how many places it sits in.

Nothing here materialises a still. A still taken on a line is an index into that line's cell
chains, so the stills holding an entry are the ones whose index falls inside the entry's
window - found by counting, with the handful that a lift moved elsewhere named separately.
"""
from bisect import bisect_left, bisect_right


class Blk:
    __slots__ = ("num", "size", "spots", "sole")

    def __init__(self, num, size):
        self.num = num
        self.size = size
        self.spots = []
        self.sole = None


class Ent:
    __slots__ = ("line", "cell", "blk", "born", "died")

    def __init__(self, line, cell, blk, born):
        self.line = line
        self.cell = cell
        self.blk = blk
        self.born = born
        self.died = None


class Kit:
    def __init__(self):
        self.g = 0
        self.charge = {}


def kit(st):
    one = getattr(st, "kit", None)
    if one is None:
        one = st.kit = Kit()
    return one


def who(st, b):
    """Every line holding this block: by a head, or by a still it owns."""
    out = set()
    top = kit(st).g
    for e in b.spots:
        line = st.lines[e.line]
        if e.died is None:
            out.add(e.line)
            hi = top
        else:
            hi = e.died
        lo = bisect_left(line.taken, e.born)
        n = bisect_right(line.taken, hi - 1) - lo
        if n <= 0:
            continue
        moved = 0
        for idx, owner in line.away:
            if e.born <= idx < hi:
                out.add(owner)
                moved += 1
        if n > moved:
            out.add(e.line)
    return out


def settle(st, b, now):
    """Move this block's size onto whichever line holds it alone, or off the books."""
    one = next(iter(now)) if len(now) == 1 else None
    if one == b.sole:
        return
    charge = kit(st).charge
    if b.sole is not None:
        charge[b.sole] -= b.size
    if one is not None:
        charge[one] = charge.get(one, 0) + b.size
    b.sole = one


def touch(st, b):
    settle(st, b, who(st, b))


def shift(st, name, idx, owner):
    """Record that the still at this index, taken on this line, is owned elsewhere now."""
    line = st.lines[name]
    keep = [(i, o) for (i, o) in line.away if i != idx]
    if owner != name:
        keep.append((idx, owner))
    keep.sort()
    line.away = keep


def sweep(st, names):
    """Every block with an entry on one of these lines is asked again who holds it."""
    seen = set()
    for name in names:
        for chain in st.lines[name].cells.values():
            for e in chain.ents:
                if id(e.blk) not in seen:
                    seen.add(id(e.blk))
                    touch(st, e.blk)
PYEOF

cat > /app/led/cost.py <<'PYEOF'
from led import hold


def blocks(st):
    seen = set()
    for one in st.lines.values():
        for chain in one.cells.values():
            for e in chain.ents:
                if id(e.blk) not in seen:
                    seen.add(id(e.blk))
                    yield e.blk


def charge(st, name):
    total = 0
    for b in blocks(st):
        if name in hold.who(st, b):
            total += b.size
    return total
PYEOF

cat > /app/led/tree.py <<'PYEOF'
"""The forest: which still a line was grafted from, which line owns which still, and the lift.

A still records the line it was taken on, which never changes, and the line that owns it,
which a lift does change. The first decides whose chains answer what the still holds; the
second decides which line is holding the blocks it holds, and that is why a lift moves a
charge without a single block being written or released.

A lift takes the stills of the line above up to and including the origin - the prefix, in the
order they were taken - hands them to the graft, and swaps the two origins, so the line above
becomes a graft of the one that was grafted from it.
"""
from led import cell, hold


class Still:
    __slots__ = ("on", "owner", "idx")

    def __init__(self, on, idx):
        self.on = on
        self.owner = on
        self.idx = idx


def freeze(st, name, still):
    """Taking a still costs nothing: the line already holds everything its head holds."""
    kit = hold.kit(st)
    one = cell.line(st, name)
    st.stills[still] = Still(name, kit.g)
    one.taken.append(kit.g)
    one.stills.append(still)
    kit.g += 1


def sprout(st, still, name):
    cell.mkline(st, name)
    one = cell.line(st, name)
    one.origin = still
    for c, b in cell.held(st, still):
        cell.plant(st, name, c, b)
        hold.touch(st, b)


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
    above = cell.line(st, st.stills[still].owner)
    cut = above.stills.index(still) + 1
    moved = above.stills[:cut]
    above.stills = above.stills[cut:]
    one.stills = moved + one.stills
    touched = set()
    for each in moved:
        rec = st.stills[each]
        rec.owner = name
        hold.shift(st, rec.on, rec.idx, name)
        touched.add(rec.on)
    one.origin = above.origin
    above.origin = still
    hold.sweep(st, touched)
PYEOF

cat > /app/led/gate.py <<'PYEOF'
"""The cap, measured against the charge the put would leave behind.

What a put adds is not what it costs. The cells it names may already hold blocks of this
line's own, and where no still is keeping one of those alive it goes when the put lands, so a
put can be the size of the whole cap and still fit. The only way to know is to have the write
stand and then read the line's charge, which is why the write is taken back rather than
predicted, and why a refused put leaves no block and takes no number.
"""
from led import cell, cost, say


def cap(st, name, size):
    cell.line(st, name).cap = size


def put(st, name, lo, hi, size):
    one = cell.line(st, name)
    made, shut = cell.write(st, name, lo, hi, size)
    if one.cap is not None and cost.charge(st, name) > one.cap:
        cell.undo(st, made, shut)
        say.full(st, name)
        return
    num = st.mint()
    for e in made:
        e.blk.num = num
PYEOF

cat > /app/led/free.py <<'PYEOF'
"""Dropping a still: what it is not allowed to take, and what actually goes.

A still that a line was grafted from is the ground that line stands on, so it stays until a
lift moves it. Otherwise the still leaves its owner's list and its index leaves the line it
was taken on, and what is released is the blocks it was holding that nothing holds any more -
which is not the same as what it held, and not the same as what no other still held, because
a head is a holder too.
"""
from led import cell, hold, say, tree


def drop(st, still):
    if tree.rooted(st, still):
        say.busy(st, still)
        return
    rec = st.stills[still]
    was = [b for _c, b in cell.held(st, still)]
    del st.stills[still]
    cell.line(st, rec.owner).stills.remove(still)
    src = cell.line(st, rec.on)
    src.taken.remove(rec.idx)
    src.away = [(i, o) for (i, o) in src.away if i != rec.idx]
    size = 0
    for b in was:
        now = hold.who(st, b)
        hold.settle(st, b, now)
        if not now:
            size += b.size
    say.gone(st, still, size)
PYEOF
