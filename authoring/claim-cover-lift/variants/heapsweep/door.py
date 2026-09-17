"""take, drop and end, with the sweep driven by a heap of each box's best candidate."""
import heapq

from hb import book, fit, lift, line, snarl, tell
from hb.desk import boxof


def take(st, job, node, mode):
    if busy(st, job):
        return
    if fit.cover(st, job, node, mode):
        book.add(st, job, node, mode)
        tell.grant(st, job, node, mode)
        return
    box = boxof(node)
    if box != node:
        up = lift.check(st, job, node, mode)
        if up is not None:
            tell.lift(st, job, box, up)
            ask(st, job, box, up, (node, mode))
            return
    ask(st, job, node, mode, None)


def busy(st, job):
    return job in st.gone or line.asked(st, job) is not None


def ask(st, job, node, mode, trig):
    if fit.blockers(st, job, node, mode):
        line.park(st, job, node, mode, trig)
        settle(st, job)
    else:
        sweep(st, give(st, {"job": job, "node": node, "mode": mode, "trig": trig}))


def give(st, req):
    book.add(st, req["job"], req["node"], req["mode"])
    tell.grant(st, req["job"], req["node"], req["mode"])
    hit = {boxof(req["node"])}
    if req["trig"] is not None:
        hit |= lift.settle(st, req["job"], req["node"], req["trig"])
    return hit


def best(st, box):
    for req in line.queued(st, box):
        if not fit.blockers(st, req["job"], req["node"], req["mode"], req["seq"]):
            return req
    return None


def sweep(st, hit):
    """A heap of (sequence, box) candidates, re-checked when it is popped."""
    heap = []
    seen = {}
    for box in hit:
        req = best(st, box)
        if req is not None:
            heapq.heappush(heap, (req["seq"], box))
            seen[box] = req["seq"]
    while heap:
        seq, box = heapq.heappop(heap)
        if seen.get(box) != seq:
            continue
        req = best(st, box)
        if req is None:
            seen.pop(box, None)
            continue
        if req["seq"] != seq:
            seen[box] = req["seq"]
            heapq.heappush(heap, (req["seq"], box))
            continue
        line.pull(st, req)
        touched = give(st, req) | {box}
        for one in touched:
            fresh = best(st, one)
            if fresh is None:
                seen.pop(one, None)
                continue
            if seen.get(one) != fresh["seq"]:
                seen[one] = fresh["seq"]
                heapq.heappush(heap, (fresh["seq"], one))


def settle(st, job):
    while True:
        bad = snarl.ring(st, job)
        if not bad:
            return
        sweep(st, snarl.kill(st, snarl.pick(st, bad)))


def drop(st, job, node):
    if busy(st, job):
        return
    if book.sub(st, job, node) is not None:
        tell.free(st, job, node)
        sweep(st, {boxof(node)})


def end(st, job):
    if busy(st, job):
        return
    hit = book.clear(st, job)
    tell.done(st, job)
    st.gone.add(job)
    sweep(st, hit)
