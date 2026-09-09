def avail(r):
    return r.shn


def refill(side, r):
    r.shn = r.rem if r.shw is None else min(r.shw, r.rem)
    q = side.lv[r.px]
    q.popleft()
    q.append(r)
    return r.shn
