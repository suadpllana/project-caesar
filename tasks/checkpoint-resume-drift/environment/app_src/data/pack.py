def fill(cx, step):
    binw = cx.cfg["binw"]
    budget = cx.cfg["budget"]
    rows = []
    cur = []
    tot = 0
    while True:
        if tot >= budget and not cur:
            break
        it = cx.feed.take()
        if it is None:
            sid = cx.feed.draw(cx.samp)
            it = (sid, cx.sched.bound(step))
        tk = cx.store.raw(it[0])[: it[1]]
        if len(cur) + len(tk) <= binw:
            cur = cur + tk
            tot += len(tk)
            if len(cur) == binw:
                rows.append(cur)
                cur = []
            continue
        rows.append(cur)
        cur = []
        if tot >= budget:
            cx.feed.hold(it[0], it[1])
            break
        cur = list(tk)
        tot += len(tk)
    if cur:
        rows.append(cur)
    return rows
