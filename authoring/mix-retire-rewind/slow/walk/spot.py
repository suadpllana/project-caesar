from feed import draw


def at(box, slot):
    got = draw.ride(box, slot)
    seen = []
    for j in range(len(box.lens)):
        if got.out[j]:
            seen.append(None)
        else:
            seen.append((got.ep[j], got.cur[j], got.took[j]))
    return seen
