from feed import deck, mix


def slots(box, at, wide):
    took = mix.took(box, at)
    start, pat, _t = mix.hold(box, at)
    span = len(pat)
    out = []
    slot = at
    while len(out) < wide:
        j = pat[(slot - start) % span]
        out.append((j, deck.pick(box, j, took[j])))
        took[j] += 1
        slot += 1
        if deck.spent(box, j, took[j]):
            start, pat, _t = mix.hold(box, slot)
            span = len(pat)
    return out
