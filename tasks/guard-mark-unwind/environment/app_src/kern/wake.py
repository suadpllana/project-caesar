from kern import pick


def rouse(f, ch):
    return pick.pick(f, ch) is not None
