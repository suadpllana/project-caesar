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
            if not fit.blockers(st, job, box, up):
                hold.add(st, job, box, up)
                say.grant(st, job, box, up)
                sweep(st, lift.settle(st, job, box, (node, mode)))
                return
    ask(st, job, node, mode)


def ask(st, job, node, mode):
    if fit.blockers(st, job, node, mode):
        line.park(st, job, node, mode, None)
        settle(st, job)
    else:
        hold.add(st, job, node, mode)
        say.grant(st, job, node, mode)
        sweep(st, {boxof(node)})


def sweep(st, hit):
    for node in sorted(st.pend):
        if boxof(node) not in hit:
            continue
        for req in line.queued(st, node):
            if fit.blockers(st, req["job"], req["node"], req["mode"]):
                break
            line.pull(st, req)
            hold.add(st, req["job"], req["node"], req["mode"])
            say.grant(st, req["job"], req["node"], req["mode"])
            if req["trig"] is not None:
                lift.settle(st, req["job"], req["node"], req["trig"])


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
