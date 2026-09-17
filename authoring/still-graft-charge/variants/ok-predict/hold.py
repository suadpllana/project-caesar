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
