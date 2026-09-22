from led import say


def shut(store, t):
    t.shift(t.taken.again(store))
    base = {}
    for k in t.taken.keys():
        base[k] = t.taken.at(k)
    held = dict(base)
    wrote = set()
    stack = []
    for ent in t.ents:
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
        elif kind == "m":
            stack.append((dict(held), set(wrote)))
        elif kind == "k" or kind == "l":
            got = held[ent[1]]
            if kind == "k":
                stands = got == ent[2]
            else:
                stands = got >= ent[2]
            if not stands:
                if not stack:
                    return say.shut_no(t.num)
                held, wrote = stack.pop()
    return say.shut_ok(t.num, store.write(wrote, held))
