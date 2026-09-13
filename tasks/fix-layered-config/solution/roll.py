"""Guards read layer starts; maps capture entry starts before clearing."""
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
        elif ent.kind == "map":
            store = pile.mapped(store, ent.a, ent.b)
        else:
            store = pile.mix(store, ent.a, ent.b, j)
    return store
