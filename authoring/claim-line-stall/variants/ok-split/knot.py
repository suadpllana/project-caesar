"""Correct variant: strongly connected parts by two walks, forward then backward."""
from hold import book, line


def blockers(h, job):
    req = h.ask.get(job)
    if req is None:
        return set()
    return book.whoclash(h, job, req[2], req[3]) | line.earlier(h, req)


def loops(h):
    out = {}
    for seed in list(h.bh):
        if True:
            stack = [seed]
            while stack:
                one = stack.pop()
                if one in out:
                    continue
                out[one] = blockers(h, one)
                stack.extend(x for x in out[one] if x not in out)
    back = {}
    for one, kids in out.items():
        for kid in kids:
            back.setdefault(kid, set()).add(one)
    order = []
    done = set()
    for one in sorted(out, key=lambda j: h.born[j]):
        if one in done:
            continue
        work = [(one, iter(out.get(one, ())))]
        done.add(one)
        while work:
            top, kids = work[-1]
            moved = False
            for kid in kids:
                if kid not in done:
                    done.add(kid)
                    work.append((kid, iter(out.get(kid, ()))))
                    moved = True
                    break
            if not moved:
                order.append(work.pop()[0])
    seen = set()
    found = set()
    for one in reversed(order):
        if one in seen:
            continue
        part = []
        stack = [one]
        seen.add(one)
        while stack:
            top = stack.pop()
            part.append(top)
            for prev in back.get(top, ()):
                if prev not in seen and prev in out:
                    seen.add(prev)
                    stack.append(prev)
        if len(part) > 1:
            found.update(part)
    return found


def pick(h, jobs):
    return min(jobs, key=lambda j: (book.owns(h, j), -h.born[j]))
