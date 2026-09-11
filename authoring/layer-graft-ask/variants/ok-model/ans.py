"""The two queries, both answered at the count the query named."""

from cfg import made, past, pile, say, work


def answer(hist, qry):
    stop = past.stop_of(hist, qry.stop)
    store = hist.store(stop)
    if qry.kind == "tot":
        return say.tot(qry.shown, pile.count(hist, store, qry.path))
    dfn = pile.find(store, qry.path)
    if dfn is None:
        return say.gone(qry.shown)
    got = work.at_path(hist, qry.path, stop)
    if got == work.GONE:
        return say.gone(qry.shown)
    if got == work.LOOP:
        return say.loop(qry.shown)
    return say.val(qry.shown, got, made.reported(dfn))
