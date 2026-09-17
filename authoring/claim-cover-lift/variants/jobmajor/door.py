"""take, drop and end, and the order the grants they free come out in."""
from hb import book, fit, lift, line, snarl, tell
from hb.desk import boxof


def take(st, job, node, mode):
    if job in st.gone or line.asked(st, job) is not None:
        return
    if fit.cover(st, job, node, mode):
        book.put(st, job, node, mode)
        tell.grant(st, job, node, mode)
        return
    trig = None
    box = boxof(node)
    if box != node:
        up = lift.check(st, job, node, mode)
        if up is not None:
            tell.lift(st, job, box, up)
            trig, node, mode = (node, mode), box, up
    if fit.blockers(st, job, node, mode):
        line.park(st, job, node, mode, trig)
        settle(st, job)
    else:
        sweep(st, hand(st, job, node, mode, trig))


def hand(st, job, node, mode, trig):
    book.put(st, job, node, mode)
    tell.grant(st, job, node, mode)
    hit = {boxof(node)}
    if trig is not None:
        hit |= lift.settle(st, job, node, trig)
    return hit


def ready(st, box):
    for ask in line.queued(st, box):
        if not fit.blockers(st, ask["job"], ask["node"], ask["mode"], ask["seq"]):
            return ask
    return None


def sweep(st, hit):
    warm = set(hit)
    while warm:
        pick = None
        for box in sorted(warm):
            ask = ready(st, box)
            if ask is None:
                warm.discard(box)
            elif pick is None or ask["seq"] < pick["seq"]:
                pick = ask
        if pick is None:
            return
        line.pull(st, pick)
        warm.add(boxof(pick["node"]))
        warm |= hand(st, pick["job"], pick["node"], pick["mode"], pick["trig"])


def settle(st, job):
    while True:
        bad = snarl.ring(st, job)
        if not bad:
            return
        sweep(st, snarl.kill(st, snarl.pick(st, bad)))


def drop(st, job, node):
    if job in st.gone or line.asked(st, job) is not None:
        return
    if book.sub(st, job, node) is not None:
        tell.free(st, job, node)
        sweep(st, {boxof(node)})


def end(st, job):
    if job in st.gone or line.asked(st, job) is not None:
        return
    hit = book.clear(st, job)
    tell.done(st, job)
    st.gone.add(job)
    sweep(st, hit)
