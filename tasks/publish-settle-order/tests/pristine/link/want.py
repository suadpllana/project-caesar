from reg import hold


def wanted(h, r):
    if hold.held(h, r.name) > 0:
        return True
    for o in h.units.values():
        if o is r:
            continue
        for other, _kind in o.needs:
            if other == r.name:
                return True
    return False
