from hb import book, fit, line, tell
from hb.desk import boxof


def step(st, job):
    req = line.asked(st, job)
    if req is None:
        return set()
    return {other for other in fit.blockers(st, job, req["node"], req["mode"])
            if line.asked(st, other) is not None}


def ring(st, job):
    seen = [job]
    one = job
    while True:
        out = sorted(step(st, one))
        if not out:
            return set()
        one = out[0]
        if one in seen:
            return set(seen[seen.index(one):])
        seen.append(one)


def pick(st, ring_):
    return sorted(ring_)[0]


def kill(st, job):
    tell.stop(st, job)
    st.gone.add(job)
    req = line.asked(st, job)
    if req is not None:
        line.pull(st, req)
    hit = book.clear(st, job)
    if req is not None:
        hit.add(boxof(req["node"]))
    return hit
