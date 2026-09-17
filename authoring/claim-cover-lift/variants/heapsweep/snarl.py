"""Jobs that have come to wait for each other, found by two breadth-first walks."""
from collections import deque

from hb import book, fit, line, tell
from hb.desk import boxof


def step(st, job):
    req = line.asked(st, job)
    if req is None:
        return set()
    return fit.blockers(st, job, req["node"], req["mode"], req["seq"])


def ring(st, job):
    if line.asked(st, job) is None:
        return set()
    out = {}
    queue = deque([job])
    while queue:
        one = queue.popleft()
        if one in out:
            continue
        out[one] = step(st, one)
        for other in out[one]:
            if other not in out:
                queue.append(other)
    back = {}
    for one, kids in out.items():
        for kid in kids:
            back.setdefault(kid, set()).add(one)
    ahead = set()
    queue = deque(out.get(job, ()))
    while queue:
        one = queue.popleft()
        if one in ahead:
            continue
        ahead.add(one)
        queue.extend(out.get(one, ()))
    home = set()
    queue = deque(back.get(job, ()))
    while queue:
        one = queue.popleft()
        if one in home:
            continue
        home.add(one)
        queue.extend(back.get(one, ()))
    return ahead & home


def pick(st, ring_):
    ranked = sorted(ring_, key=lambda one: (book.count(st, one), -int(one[1:])))
    return ranked[0]


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
