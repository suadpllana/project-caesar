"""The two queries."""

from cfg import made, past, pile, say, work

WORD = {work.GONE: say.gone, work.LOOP: say.loop}


def answer(hist, qry):
    stop = past.stop_of(hist, qry.stop)
    store = hist.store(stop)
    if qry.kind == "tot":
        return say.tot(qry.shown, pile.count(store, qry.path))
    dfn = pile.find(store, qry.path)
    if dfn is None:
        return say.gone(qry.shown)
    got = work.at_def(hist, dfn, stop)
    if isinstance(got, int):
        return say.val(qry.shown, got, made.reported(dfn))
    return WORD[got](qry.shown)
