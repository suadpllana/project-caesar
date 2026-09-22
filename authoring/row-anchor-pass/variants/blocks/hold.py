"""The item the frame holds still, and how it survives an edit.

The hold is chosen at the anchor line - the bottom of the band - not at the top of the pane.
The pane can only hold something it has actually laid out: a header, or a row it remembers. When
the row across the line is one it does not remember, its place is only a guess built from a
carried height, so the hold is the nearest item above the line that is a header or a remembered
row, and the gap can be far below zero. The gap is the held item's top less the line.

The hold is taken before the source changes. When a delete removes it, it walks to the first item
that survives after the removed rows - the last that survives before them when nothing follows -
with the gap moved by the difference of those two tops as they stood before the edit. A hold
carried that way may land on a row the pane does not remember; only the choice at the line is
restricted.
"""


def take(gm, line):
    i = gm.at(line)
    while not gm.holdable(i):
        i -= 1
    return i, gm.key(i), gm.top(i) - line


def track(gm, held, ev):
    kind, gid, pos, n = ev
    i, _key, gap = held
    first = gm.gbase(gm.gindex(gid)) + 1 + pos
    if kind == "ins":
        gm.ins(gid, pos, n)
        if i >= first:
            i += n
        return i, gm.key(i), gap
    if first <= i < first + n:
        after = first + n
        if after < gm.count():
            gap += gm.top(after) - gm.top(i)
            gm.dele(gid, pos, n)
            return first, gm.key(first), gap
        back = first - 1
        gap += gm.top(back) - gm.top(i)
        gm.dele(gid, pos, n)
        return back, gm.key(back), gap
    gm.dele(gid, pos, n)
    if i >= first + n:
        i -= n
    return i, gm.key(i), gap
