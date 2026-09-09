from reg import hold, order


def joined(h, r):
    return None


def tied(h, r, t):
    r.ties.append(t.name)


def parted(h, r):
    names = [other for other, kind in r.needs if kind] + r.ties
    r.ties = []
    return names


def wanted(h, r):
    if hold.held(h, r.name) > 0:
        return True
    for o in order.live(h):
        if o is r:
            continue
        if r.name in o.ties:
            return True
        for other, kind in o.needs:
            if kind and other == r.name:
                return True
    return False
