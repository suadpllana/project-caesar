from hold import book


def blockers(h, job):
    req = h.ask.get(job)
    if req is None:
        return set()
    return book.whoclash(h, job, req[2], req[3])


def loops(h):
    edge = {}
    for job in h.ask:
        edge[job] = blockers(h, job)
    out = set()
    for start in edge:
        seen = set()
        front = list(edge.get(start, ()))
        while front:
            one = front.pop()
            if one == start:
                out.add(start)
                break
            if one in seen:
                continue
            seen.add(one)
            front.extend(edge.get(one, ()))
    return out


def pick(h, jobs):
    return max(jobs, key=lambda j: h.born[j])
