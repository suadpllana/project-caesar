"""The pool of pages: what is free, what is reusable, and what a take-back costs.

Three states, and every page is in exactly one of them. Held: some request has it in its
residency. Reusable: nobody holds it, it is complete, and a walk from the start of a prompt
can still reach it. Free: in the pool, available to the next allocation.

The take-back is the part the first plan gets wrong. Taking one page back takes with it
every page below it - those nobody holds go straight back to the pool, those somebody holds
stay alive and out of reach until their holder lets go - and a page that was still being
written when that happened is below it too. So a take-back is not a queue pop: pages leave
the reusable set in groups, from the middle, for a reason somewhere else in the tree.
"""
import heapq
from kv import keep


def start(kv):
    kv.fr = list(range(1, kv.n + 1))
    heapq.heapify(kv.fr)
    kv.ref = {}
    kv.use = {}
    keep.start(kv)


def grab(kv):
    """One page, by the order of supply: free, then a take-back, then nothing."""
    if not kv.fr and kv.use:
        back(kv)
    if not kv.fr:
        return 0
    return heapq.heappop(kv.fr)


def hold(kv, pid):
    """One more holder. A page that was reusable stops being reusable."""
    c = kv.ref.get(pid, 0)
    if c == 0:
        kv.use.pop(pid, None)
    kv.ref[pid] = c + 1


def rest(kv, pid):
    """One holder fewer. The last one leaving decides reusable against free."""
    c = kv.ref.get(pid, 0) - 1
    kv.ref[pid] = c
    if c > 0:
        return
    pg = kv.pg.get(pid)
    if pg is not None and pg.n == kv.w and kv.ok.get(pid):
        kv.use[pid] = kv.tick()
    else:
        loose(kv, pid)


def free(kv, pid):
    kv.pg.pop(pid, None)
    kv.ref.pop(pid, None)
    kv.ok.pop(pid, None)
    kv.use.pop(pid, None)
    heapq.heappush(kv.fr, pid)


def loose(kv, pid):
    """Out of the tree, with everything below it, and back to the pool where it can be."""
    gone = 0
    stack = [pid]
    while stack:
        q = stack.pop()
        stack.extend(kv.kid.pop(q, ()))
        keep.cut(kv, q)
        if kv.ref.get(q, 0) == 0:
            free(kv, q)
            gone += 1
        else:
            kv.ok[q] = False
    return gone


def back(kv):
    """Take back the page released longest ago."""
    pid = min(kv.use, key=kv.use.get)
    kv.use.pop(pid)
    kv.say("gone", pid, loose(kv, pid))
