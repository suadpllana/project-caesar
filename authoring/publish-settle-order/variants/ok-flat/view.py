from link import walk


def keys(h, *a):
    return getattr(walk, "keys")(h, *a)
