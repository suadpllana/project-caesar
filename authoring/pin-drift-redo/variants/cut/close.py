from led import say


def derive(ents, taken):
    base = {}
    for k in taken.keys():
        base[k] = taken.at(k)
    held = dict(base)
    wrote = set()
    for at, ent in enumerate(ents):
        kind = ent[0]
        if kind == "p":
            held[ent[1]] = ent[2]
            wrote.add(ent[1])
        elif kind == "a":
            held[ent[1]] = held[ent[1]] + ent[2]
            wrote.add(ent[1])
        elif kind == "c":
            held[ent[1]] = held[ent[2]]
            wrote.add(ent[1])
        elif kind == "r":
            held[ent[1]] = base[ent[2]]
            wrote.add(ent[1])
        elif kind == "f":
            held[ent[1]] = ent[2]
        elif kind == "k" or kind == "l":
            got = held[ent[1]]
            if kind == "k":
                stands = got == ent[2]
            else:
                stands = got >= ent[2]
            if not stands:
                return held, wrote, at
    return held, wrote, None


def shut(store, t):
    t.taken.again(store)
    ents = list(t.ents)
    while True:
        held, wrote, bad = derive(ents, t.taken)
        if bad is None:
            return say.shut_ok(t.num, store.write(wrote, held))
        mark = None
        for at in range(bad - 1, -1, -1):
            if ents[at][0] == "m":
                mark = at
                break
        if mark is None:
            return say.shut_no(t.num)
        ents = ents[:mark] + ents[bad + 1:]
