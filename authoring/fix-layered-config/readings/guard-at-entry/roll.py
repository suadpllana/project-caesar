"""One layer: guards read the layer start; every other entry acts on what the last one left."""
from cfg import made, pile, work


def run(hist, j, ents):
    store = hist.store(j)
    for ent in ents:
        if ent.guard is not None and not work.guard_in(hist, ent.guard, store):
            continue
        if ent.kind == "put":
            store = pile.put(store, ent.a, made.make(ent.expr, j))
        elif ent.kind == "cut":
            store = pile.cut(store, ent.a)
        elif ent.kind == "mix":
            store = pile.mix(store, ent.a, ent.b)
        elif ent.kind == "map":
            store = pile.mapped(store, ent.a, ent.b)
        else:
            store = pile.tie(store, ent.a, ent.b)
    return store
