def take(h, name):
    h.holds[name] = h.holds.get(name, 0) + 1


def give(h, name):
    h.holds[name] = h.holds.get(name, 0) - 1


def held(h, name):
    return h.holds.get(name, 0)
