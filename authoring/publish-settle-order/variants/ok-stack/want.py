from reg import hold, order


def wanted(h, r):
    if hold.held(h, r.name) > 0:
        return True
    return any(any(k and n == r.name for n, k in o.needs)
               for o in order.live(h) if o is not r)
