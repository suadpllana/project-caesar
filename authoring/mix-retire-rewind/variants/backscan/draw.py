from feed import deck, mix


def slots(box, at, wide):
    took = mix.took(box, at)
    out = []
    slot = at
    while len(out) < wide:
        j = mix.turn(box, slot)
        out.append((j, deck.pick(box, j, took[j])))
        took[j] += 1
        slot += 1
    return out
