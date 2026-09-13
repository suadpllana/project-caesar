from cfg import made, pile, work


def run(hist, store, j, ents):
    for ent in ents:
        if ent.guard is not None and not work.guard_holds(hist, store, ent.guard, j):
            continue
        if ent.kind == "put":
            store = pile.put(store, ent.a, made.make(ent.expr, j))
        elif ent.kind == "cut":
            store = pile.cut(store, ent.a)
        else:
            store = pile.mix(store, ent.a, ent.b, j)
    return store
