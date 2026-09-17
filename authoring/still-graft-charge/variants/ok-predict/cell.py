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
