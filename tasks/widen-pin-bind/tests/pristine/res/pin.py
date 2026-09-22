from res import kind


def settle(prog, sources):
    high = sources[0]
    for one in sources[1:]:
        if kind.steps(prog, high, one) is not None:
            high = one
    return high
