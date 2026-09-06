from mem import roots as rootsrc


def roots(h, full):
    return sorted(set(rootsrc.named(h)))
