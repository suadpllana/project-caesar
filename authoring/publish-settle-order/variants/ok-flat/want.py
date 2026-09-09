from link import walk


def wanted(h, *a):
    return getattr(walk, "wanted")(h, *a)
