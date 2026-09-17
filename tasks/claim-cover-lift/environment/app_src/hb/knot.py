from hb import fit, hold, line, say
from hb.store import boxof


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
    say.stop(st, job)
    st.gone.add(job)
    req = line.asked(st, job)
    if req is not None:
        line.pull(st, req)
    hit = hold.clear(st, job)
    if req is not None:
        hit.add(boxof(req["node"]))
    return hit
