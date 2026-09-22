"""The item the frame holds still, and how it survives an edit.

The hold is the item lying across the anchor line, not the first visible item: the band covers
the top of the pane, so the first visible item is usually behind it and moving that one keeps
the wrong thing still. The gap is the item's top measured from the line, so it is zero or
negative, and it is what the settle loop solves the offset back to.

An edit is where the ordering matters. The hold is taken before the source changes, and when
the edit removes it the hold walks to the first item that survives after it - the last that
survives before it when nothing does - with the gap moved by the difference of those two tops
as they stood before the edit. Reading either top after the edit reads a document the hold was
never taken against.
"""


def take(gm, line):
    i = gm.at(line)
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
