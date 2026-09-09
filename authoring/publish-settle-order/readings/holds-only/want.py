from reg import hold


def joined(h, r):
    return None


def tied(h, r, t):
    return None


def parted(h, r):
    return []


def wanted(h, r):
    return hold.held(h, r.name) > 0
