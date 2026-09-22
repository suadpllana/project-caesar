"""Correct variant: the hold as a small record, and the edit handled as an index remap.

Same contract as the reference: the item across the anchor line, the gap measured from that
line, the hold read before the source changes and the gap moved by tops taken before it.
"""


class Hold:
    __slots__ = ("i", "key", "gap")

    def __init__(self, i, key, gap):
        self.i = i
        self.key = key
        self.gap = gap


def take(gm, line):
    i = gm.at(line)
    return Hold(i, gm.key(i), gm.top(i) - line)


def track(gm, held, ev):
    kind, gid, pos, n = ev
    first = gm.gbase(gm.gindex(gid)) + 1 + pos
    removed = range(first, first + n) if kind == "del" else range(0)

    if held.i in removed:
        successor = first + n if first + n < gm.count() else first - 1
        shift = gm.top(successor) - gm.top(held.i)
        landing = first if successor >= first + n else successor
        gm.dele(gid, pos, n)
        return Hold(landing, gm.key(landing), held.gap + shift)

    if kind == "ins":
        gm.ins(gid, pos, n)
        moved = held.i + n if held.i >= first else held.i
    else:
        gm.dele(gid, pos, n)
        moved = held.i - n if held.i >= first + n else held.i
    return Hold(moved, gm.key(moved), held.gap)
