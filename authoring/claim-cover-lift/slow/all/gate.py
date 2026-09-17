from hb import fit, hold, knot, lift, line, say
from hb.store import boxof


def take(st, job, node, mode):
    if job in st.gone:
        return
    if fit.cover(st, job, node, mode):
        hold.add(st, job, node, mode)
        say.grant(st, job, node, mode)
        return
    box = boxof(node)
    if box != node:
        up = lift.check(st, job, node, mode)
        if up is not None:
            say.lift(st, job, box, up)
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
    hold.add(st, req["job"], req["node"], req["mode"])
    say.grant(st, req["job"], req["node"], req["mode"])
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
    while True:
        best = None
        for box in sorted(st.pend):
            cand = first(st, box)
            if cand is not None and (best is None or cand["seq"] < best["seq"]):
                best = cand
        if best is None:
            return
        line.pull(st, best)
        give(st, best)


def settle(st, job):
    while True:
        bad = knot.ring(st, job)
        if not bad:
            return
        sweep(st, knot.kill(st, knot.pick(st, bad)))


def drop(st, job, node):
    if job in st.gone:
        return
    if hold.sub(st, job, node) is not None:
        say.free(st, job, node)
        sweep(st, {boxof(node)})


def end(st, job):
    if job in st.gone:
        return
    hit = hold.clear(st, job)
    say.done(st, job)
    st.gone.add(job)
    sweep(st, hit)
