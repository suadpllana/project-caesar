from reg import hold


def wanted(h, r):
    return hold.held(h, r.name) > 0
