"""Correct variant: one walk out of every job, asking only whether it comes back."""
from hold import book, line


def blockers(h, job):
    req = h.ask.get(job)
    if req is None:
        return set()
    return book.whoclash(h, job, req[2], req[3]) | line.earlier(h, req)


def loops(h):
    edges = {}
    stack = list(h.bh)
    while stack:
        one = stack.pop()
        if one in edges:
            continue
        edges[one] = blockers(h, one)
        for nxt in edges[one]:
            if nxt not in edges:
                stack.append(nxt)
    found = set()
    for start in edges:
        seen = set()
        front = list(edges[start])
        while front:
            one = front.pop()
            if one == start:
                found.add(start)
                break
            if one in seen:
                continue
            seen.add(one)
            front.extend(edges.get(one, ()))
    return found


def pick(h, jobs):
    return min(jobs, key=lambda j: (book.owns(h, j), -h.born[j]))
