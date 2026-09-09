from reg import hold, order


def joined(h, r):
    return None


def parted(h, r):
    return [other for other, kind in r.needs if kind]


def wanted(h, r):
    if hold.held(h, r.name) > 0:
        return True
    for o in order.live(h):
        if o is r:
            continue
        for other, kind in o.needs:
            if kind and other == r.name:
                return True
    return False
