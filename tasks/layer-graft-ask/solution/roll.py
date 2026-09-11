"""Applying one layer.

The entries of a layer are taken in the order they were written, each against the store the
earlier ones have left. A guard is not: it is a question about the plan before the whole
layer, so it is answered against the store this layer started from, at this layer's stop. The
two rules pull in opposite directions on purpose - an entry can be taken because of a path an
earlier entry of its own layer has already removed.
"""

from cfg import made, pile, work


def run(hist, j, ents):
    store = hist.store(j)
    for ent in ents:
        if ent.guard is not None and not work.guard_holds(hist, ent.guard, j):
            continue
        if ent.kind == "put":
            store = pile.put(store, ent.a, made.make(ent.expr, j))
        elif ent.kind == "cut":
            store = pile.cut(store, ent.a)
        else:
            store = pile.mix(store, ent.a, ent.b, j)
    return store
