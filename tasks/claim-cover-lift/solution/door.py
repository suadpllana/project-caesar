from hb import book, fit, lift, line, snarl, tell
from hb.desk import boxof


def busy(st, job):
    return job in st.gone or line.asked(st, job) is not None


def take(st, job, node, mode):
    if busy(st, job):
        return
    if fit.cover(st, job, node, mode):
        book.add(st, job, node, mode)
        tell.grant(st, job, node, mode)
        return
    box = boxof(node)
    if box != node:
        up = lift.check(st, job, node, mode)
        if up is not None:
            tell.lift(st, job, box, up)
            ask(st, job, box, up, (node, mode))
            return
    ask(st, job, node, mode, None)


def ask(st, job, node, mode, trig):
    if fit.blockers(st, job, node, mode):
        line.park(st, job, node, mode, trig)
        settle(st, job)
    else:
        sweep(st, give(st, {"job": job, "node": node, "mode": mode, "trig": trig}))


def give(st, req):
    book.add(st, req["job"], req["node"], req["mode"])
    tell.grant(st, req["job"], req["node"], req["mode"])
    hit = {boxof(req["node"])}
    if req["trig"] is not None:
        hit |= lift.settle(st, req["job"], req["node"], req["trig"])
    return hit


def first(st, box):
    for req in line.queued(st, box):
        if not fit.blockers(st, req["job"], req["node"], req["mode"], req["seq"]):
            return req
    return None


def sweep(st, hit):
    live = set(hit)
    while live:
        best = None
        for box in list(live):
            cand = first(st, box)
            if cand is None:
                live.discard(box)
            elif best is None or cand["seq"] < best["seq"]:
                best = cand
        if best is None:
            return
        line.pull(st, best)
        live.add(boxof(best["node"]))
        live |= give(st, best)


def settle(st, job):
    while True:
        bad = snarl.ring(st, job)
        if not bad:
            return
        sweep(st, snarl.kill(st, snarl.pick(st, bad)))


def drop(st, job, node):
    if busy(st, job):
        return
    if book.sub(st, job, node) is not None:
        tell.free(st, job, node)
        sweep(st, {boxof(node)})


def end(st, job):
    if busy(st, job):
        return
    hit = book.clear(st, job)
    tell.done(st, job)
    st.gone.add(job)
    sweep(st, hit)
