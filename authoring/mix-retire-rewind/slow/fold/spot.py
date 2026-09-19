from feed import deck, mix


def at(box, slot):
    took = mix.took(box, slot)
    seen = []
    for j in range(len(box.lens)):
        if box.hold[j] and took[j] >= deck.fits(box, j) * box.hold[j]:
            seen.append(None)
        else:
            ep, cur = deck.at(box, j, took[j])
            seen.append((ep, cur, took[j]))
    return seen
