import heapq

from kv import keep


def start(kv):
    kv.fr = list(range(1, kv.n + 1))
    heapq.heapify(kv.fr)
    kv.ref = {}
    kv.use = {}
    keep.start(kv)


def grab(kv):
    if not kv.fr and kv.use:
        back(kv)
    if not kv.fr:
        return 0
    return heapq.heappop(kv.fr)


def hold(kv, pid):
    c = kv.ref.get(pid, 0)
    if c == 0:
        kv.use.pop(pid, None)
    kv.ref[pid] = c + 1


def rest(kv, pid):
    c = kv.ref.get(pid, 0) - 1
    kv.ref[pid] = c
    if c > 0:
        return
    pg = kv.pg.get(pid)
    if pg is not None and pg.n == kv.w:
        kv.use[pid] = 1
    else:
        free(kv, pid)


def free(kv, pid):
    keep.cut(kv, pid)
    kv.pg.pop(pid, None)
    kv.ref.pop(pid, None)
    kv.use.pop(pid, None)
    heapq.heappush(kv.fr, pid)


def back(kv):
    pid = min(kv.use)
    kv.use.pop(pid)
    free(kv, pid)
    kv.say("gone", pid, 1)
