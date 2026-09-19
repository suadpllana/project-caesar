from feed import deck, draw


def at(box, slot):
    got = draw.ride(box, slot + 1)
    seen = []
    for j in range(len(box.lens)):
        if got.out[j]:
            seen.append(None)
        else:
            ep, cur = deck.at(box, j, got.took[j])
            seen.append((ep, cur, got.took[j]))
    return seen
