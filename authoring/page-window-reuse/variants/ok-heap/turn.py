"""One step: every resident request decodes a token, then waiting prompts are filled, and
the whole of it inside one token budget.

Waiting prompts are taken in arrival order and the phase stops at the first one that cannot
take a page this step, so nothing jumps the queue. A page that cannot be supplied ends the
step: the request that became resident most recently gives everything back and starts again
from nothing later - and what it gives back
is reusable rather than free, so the allocation that forced it still has to take a page
back, usually one belonging to somebody else.
"""
from kv import fill, live, put


def order(kv, name):
    seq = kv.rq[name].seq
    at = 0
    while at < len(kv.wait) and kv.rq[kv.wait[at]].seq < seq:
        at += 1
    kv.wait.insert(at, name)


def hold(kv, rq):
    who = kv.rq[kv.on[-1]] if kv.on else rq
    kv.say("hold", who.name)
    live.clear(kv, who)
    who.fed = 0
    who.made = 0
    who.got = False
    who.up = -1
    if who.name in kv.on:
        kv.on.remove(who.name)
    if who.name not in kv.wait:
        order(kv, who.name)


def fin(kv, rq):
    live.clear(kv, rq)
    kv.on.remove(rq.name)
    kv.say("done", rq.name)


def kill(kv, name):
    rq = kv.rq.get(name)
    if rq is None:
        return
    live.clear(kv, rq)
    if name in kv.on:
        kv.on.remove(name)
    if name in kv.wait:
        kv.wait.remove(name)
    del kv.rq[name]


def decode(kv, b):
    for name in kv.on[:b]:
        rq = kv.rq.get(name)
        if rq is None:
            continue
        if not put.write(kv, rq, rq.out[rq.made]):
            hold(kv, rq)
            return -1
        rq.made += 1
        b -= 1
        live.trim(kv, rq)
        if rq.made == len(rq.out):
            fin(kv, rq)
    return b


def step(kv):
    b = decode(kv, kv.b)
    if b < 0:
        return
    while b > 0 and kv.wait:
        rq = kv.rq[kv.wait[0]]
        used, ok, more = fill.feed(kv, rq, b)
        if not ok:
            hold(kv, rq)
            return
        if not more:
            return
        b -= used
