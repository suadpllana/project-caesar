"""Select and evaluate against the same layer view, reporting put origin."""
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
