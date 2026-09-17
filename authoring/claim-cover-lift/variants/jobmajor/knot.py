"""Jobs that have come to wait for each other, by strongly connected components."""
from hb import fit, hold, line, say
from hb.store import boxof


def edges(st, job):
    ask = line.asked(st, job)
    if ask is None:
        return set()
    return fit.blockers(st, job, ask["node"], ask["mode"], ask["seq"])


def ring(st, job):
    """Tarjan over the part of the relation reachable from this job."""
    if line.asked(st, job) is None:
        return set()
    index, low, on, stack, parts = {}, {}, set(), [], []
    work = [(job, iter(sorted(edges(st, job))))]
    index[job] = low[job] = 0
    stack.append(job)
    on.add(job)
    step = 1
    while work:
        top, kids = work[-1]
        moved = False
        for kid in kids:
            if kid not in index:
                index[kid] = low[kid] = step
                step += 1
                stack.append(kid)
                on.add(kid)
                work.append((kid, iter(sorted(edges(st, kid)))))
                moved = True
                break
            if kid in on:
                low[top] = min(low[top], index[kid])
        if moved:
            continue
        work.pop()
        if work:
            low[work[-1][0]] = min(low[work[-1][0]], low[top])
        if low[top] == index[top]:
            part = []
            while True:
                one = stack.pop()
                on.discard(one)
                part.append(one)
                if one == top:
                    break
            if len(part) > 1:
                parts.append(set(part))
    for part in parts:
        if job in part:
            return part
    return set()


def pick(st, ring_):
    return min(ring_, key=lambda one: (hold.count(st, one), -int(one[1:])))


def kill(st, job):
    say.stop(st, job)
    st.gone.add(job)
    ask = line.asked(st, job)
    hit = set()
    if ask is not None:
        line.pull(st, ask)
        hit.add(boxof(ask["node"]))
    return hit | hold.clear(st, job)
