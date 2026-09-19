from feed import deck, mix


def slots(box, at, wide):
    out = []
    for slot in range(at, at + wide):
        j = mix.turn(box, slot)
        out.append((j, deck.pick(box, j, mix.took(box, slot)[j])))
    return out
