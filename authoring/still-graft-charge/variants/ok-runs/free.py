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
    hold.recut(st, rec.on)
    size = 0
    for b in was:
        now = hold.who(st, b)
        hold.settle(st, b, now)
        if not now:
            size += b.size
    say.gone(st, still, size)
