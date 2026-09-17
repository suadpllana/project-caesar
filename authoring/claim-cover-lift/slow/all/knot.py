from hb import fit, hold, line, say
from hb.store import boxof


def step(st, job):
    req = line.asked(st, job)
    if req is None:
        return set()
    return fit.blockers(st, job, req["node"], req["mode"], req["seq"])


def ring(st, job):
    if line.asked(st, job) is None:
        return set()
    edges = {}
    stack = [job]
    while stack:
        one = stack.pop()
        if one in edges:
            continue
        out = step(st, one)
        edges[one] = out
        for other in out:
            if other not in edges:
                stack.append(other)
    back = {}
    for one, out in edges.items():
        for other in out:
            back.setdefault(other, set()).add(one)
    reach = set()
    stack = list(back.get(job, ()))
    while stack:
        one = stack.pop()
        if one in reach:
            continue
        reach.add(one)
        stack.extend(back.get(one, ()))
    ahead = set()
    stack = list(edges.get(job, ()))
    while stack:
        one = stack.pop()
        if one in ahead:
            continue
        ahead.add(one)
        stack.extend(edges.get(one, ()))
    return ahead & reach


def pick(st, ring_):
    best = None
    for job in ring_:
        key = (hold.count(st, job), -int(job[1:]))
        if best is None or key < best[0]:
            best = (key, job)
    return best[1]


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
