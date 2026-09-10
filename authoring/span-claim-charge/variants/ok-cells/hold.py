"""Spans and the block references on them, one per block."""
from store import dev, tally


class Span:
    __slots__ = ("at", "wide", "hits", "by", "live", "paths", "lca")

    def __init__(self, at, wide):
        self.at = at
        self.wide = wide
        self.hits = {}
        self.by = {}
        self.live = 0
        self.paths = []
        self.lca = None


class Item:
    __slots__ = ("line", "name", "cell")

    def __init__(self, line, name):
        self.line = line
        self.name = name
        self.cell = []


def setup(st):
    return None


def hook(st, line, sp, off):
    sp.live += 1
    sp.hits[off] = sp.hits.get(off, 0) + 1
    seen = sp.by.get(line, 0)
    sp.by[line] = seen + 1
    if not seen:
        tally.gain(st, line, sp)


def unhook(st, line, sp, off):
    sp.live -= 1
    left = sp.hits[off] - 1
    if left:
        sp.hits[off] = left
    else:
        del sp.hits[off]
    seat = sp.by[line] - 1
    if seat:
        sp.by[line] = seat
        return
    del sp.by[line]
    tally.lose(st, line, sp)


def bury(st, seen):
    rel = 0
    for sp in seen:
        if not sp.live:
            dev.give(st, sp.at, sp.wide)
            rel += sp.wide
    return rel


def strip(st, it, lo, hi, seen):
    for i in range(lo, hi):
        cell = it.cell[i]
        if cell is None:
            continue
        unhook(st, it.line, cell[0], cell[1])
        seen.add(cell[0])
        it.cell[i] = None


def doomed(it, spots):
    count = {}
    for i in spots:
        cell = it.cell[i]
        if cell is not None:
            count[cell[0]] = count.get(cell[0], 0) + 1
    return sum(sp.wide for sp, k in count.items() if k == sp.live)


def fill(st, it, spots, parts):
    made = [Span(at, wide) for at, wide in parts]
    k = 0
    off = 0
    for i in spots:
        sp = made[k]
        it.cell[i] = (sp, off)
        hook(st, it.line, sp, off)
        off += 1
        if off == sp.wide:
            k += 1
            off = 0
