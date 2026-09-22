"""Giving way, and what the loser keeps.

A holder younger than the requester does not block it; it gives its grant up on the spot,
and because the cover it held above is the permission for everything it held below, the
whole subtree goes with it, deepest first.

What it leaves behind is the point. A grant that existed only because something below it
needed a cover leaves nothing, since retaking the things below will produce it again. Only a
node the program asked for leaves a claim, at the asked mode rather than at the effective
mode that was printed, because the effective mode is derived and will be derived again from
whatever actually comes back.
"""
from lk import mode


def hand(book, due, u, res, out):
    for node, asked in book.strip(u, res, out, "give"):
        if asked is not None:
            due.claim(u, node, asked, None)
