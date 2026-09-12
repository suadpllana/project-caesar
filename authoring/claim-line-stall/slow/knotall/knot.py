"""Which jobs can never proceed, and which of them the service gives up on.

A job is held up by another when its ask is refused because that other job holds a
conflicting claim or has a conflicting ask standing ahead of it. Both halves matter: the
refusals by a job that holds nothing at all are exactly the edges a relation drawn over held
claims is missing, and they are what close the short loops.

The search is seeded from the jobs that hold a claim and also have an ask waiting. Every
loop contains one of them: an ask standing ahead of another is filed under a smaller number
inside the same group, so the refusals by waiting asks alone run strictly backwards down the
line and cannot close on themselves. A loop therefore uses at least one refusal by a held
claim, and the job that claim belongs to must have an ask of its own to carry the loop on.
"""
from hold import book, line, name


def blockers(h, job):
    req = h.ask.get(job)
    if req is None:
        return set()
    out = book.whoclash(h, job, req[2], req[3])
    mine = line.rankof(h, req)
    for fid, other in h.byunit.get(name.cut(req[2])[0], {}).items():
        if fid == req[0] or other[1] == job:
            continue
        if not book.overlap(req[2], other[2]) or not book.clash(req[3], other[3]):
            continue
        if line.rankof(h, other) < mine:
            out.add(other[1])
    return out


def loops(h):
    """Every job that following held-up-by can reach from itself."""
    idx, low, onstack, stack, found = {}, {}, {}, [], set()
    count = 0
    for seed in sorted(h.ask, key=lambda j: h.born[j]):
        if seed in idx:
            continue
        idx[seed] = low[seed] = count
        count += 1
        stack.append(seed)
        onstack[seed] = True
        work = [(seed, iter(blockers(h, seed)))]
        while work:
            top, kids = work[-1]
            down = False
            for kid in kids:
                if kid not in idx:
                    idx[kid] = low[kid] = count
                    count += 1
                    stack.append(kid)
                    onstack[kid] = True
                    work.append((kid, iter(blockers(h, kid))))
                    down = True
                    break
                if onstack.get(kid):
                    low[top] = min(low[top], idx[kid])
            if down:
                continue
            work.pop()
            if work:
                up = work[-1][0]
                low[up] = min(low[up], low[top])
            if low[top] == idx[top]:
                part = []
                while True:
                    one = stack.pop()
                    onstack[one] = False
                    part.append(one)
                    if one == top:
                        break
                if len(part) > 1:
                    found.update(part)
    return found


def pick(h, jobs):
    return min(jobs, key=lambda j: (len(h.held.get(j) or ()), -h.born[j]))
