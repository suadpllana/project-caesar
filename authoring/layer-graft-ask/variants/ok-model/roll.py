"""Applying a layer: every guard of it answered first, then the entries it kept.

Answering all the guards before applying anything is only equivalent to answering each as its
entry comes up because a guard reads the plan before the whole layer; doing it this way makes
that rule impossible to get wrong by accident.
"""

from cfg import made, pile, work


def run(hist, j, ents):
    kept = [e for e in ents if e.guard is None or work.guard_holds(hist, e.guard, j)]
    store = hist.store(j)
    for ent in kept:
        if ent.kind == "put":
            store = pile.put(store, ent.a, made.make(ent.expr, j))
        elif ent.kind == "cut":
            store = pile.cut(store, ent.a)
        else:
            store = pile.mix(store, ent.a, ent.b, j)
    return store
