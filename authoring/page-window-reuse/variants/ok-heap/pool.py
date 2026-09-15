import heapq

from kv import keep


def start(kv):
    kv.fr = list(range(1, kv.n + 1))
    heapq.heapify(kv.fr)
    kv.ref = {}
    kv.age = []
    kv.when = {}
    kv.clock = 0
    keep.start(kv)


def grab(kv):
    if not kv.fr and oldest(kv):
        back(kv)
    if not kv.fr:
        return 0
    return heapq.heappop(kv.fr)


def oldest(kv):
    while kv.age:
        when, pid = kv.age[0]
        if kv.when.get(pid) == when and kv.ref.get(pid, 0) == 0:
            return pid
        heapq.heappop(kv.age)
    return 0


def hold(kv, pid):
    if kv.ref.get(pid, 0) == 0:
        kv.when.pop(pid, None)
    kv.ref[pid] = kv.ref.get(pid, 0) + 1


def rest(kv, pid):
    left = kv.ref.get(pid, 0) - 1
    kv.ref[pid] = left
    if left > 0:
        return
    pg = kv.pg.get(pid)
    if pg is not None and pg.n == kv.w and kv.ok.get(pid):
        kv.clock += 1
        kv.when[pid] = kv.clock
        heapq.heappush(kv.age, (kv.clock, pid))
    else:
        loose(kv, pid)


def free(kv, pid):
    kv.pg.pop(pid, None)
    kv.ref.pop(pid, None)
    kv.ok.pop(pid, None)
    kv.when.pop(pid, None)
    heapq.heappush(kv.fr, pid)


def loose(kv, pid):
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
    pid = oldest(kv)
    kv.when.pop(pid, None)
    kv.say("gone", pid, loose(kv, pid))
