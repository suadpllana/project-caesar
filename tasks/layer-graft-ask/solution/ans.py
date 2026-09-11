"""Answering the two queries.

A query names how much of the plan counts, and that one number settles both halves of the
answer: which definition is standing at the path, and what that definition says. Splitting
them - taking the definition from the named layer and the value from the finished plan - is
the reading this file exists to get right.

The layer printed is the one that wrote the definition answering, which after a copy is not
the layer that made the copy.
"""

from cfg import made, past, pile, say, work


def answer(hist, qry):
    stop = past.stop_of(hist, qry.stop)
    store = hist.store(stop)
    if qry.kind == "tot":
        return say.tot(qry.shown, pile.count(store, qry.path))
    dfn = pile.find(store, qry.path)
    if dfn is None:
        return say.gone(qry.shown)
    got = work.at_def(hist, dfn, stop)
    if got == work.GONE:
        return say.gone(qry.shown)
    if got == work.LOOP:
        return say.loop(qry.shown)
    return say.val(qry.shown, got, made.reported(dfn))
