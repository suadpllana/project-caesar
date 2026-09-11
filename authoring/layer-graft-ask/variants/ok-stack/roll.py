"""One layer, entry by entry, with each guard answered before the layer moved."""

from cfg import made, pile, work

APPLY = {
    "put": lambda store, ent, j: pile.put(store, ent.a, made.make(ent.expr, j)),
    "cut": lambda store, ent, j: pile.cut(store, ent.a),
    "mix": lambda store, ent, j: pile.mix(store, ent.a, ent.b, j),
}


def run(hist, j, ents):
    store = hist.store(j)
    for ent in ents:
        if ent.guard is None or work.guard_holds(hist, ent.guard, j):
            store = APPLY[ent.kind](store, ent, j)
    return store
