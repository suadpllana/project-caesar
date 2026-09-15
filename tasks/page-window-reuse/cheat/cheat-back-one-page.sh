#!/bin/bash
# a take-back leaves what is below it alone
set -euo pipefail

cat > /app/kv/pool.py <<'PYEOF'
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
from collections import OrderedDict

from kv import keep


def start(kv):
    kv.fr = list(range(1, kv.n + 1))
    heapq.heapify(kv.fr)
    kv.ref = {}
    kv.use = OrderedDict()
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
        kv.use[pid] = 1
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
        kv.kid.pop(q, ())
        keep.cut(kv, q)
        if kv.ref.get(q, 0) == 0:
            free(kv, q)
            gone += 1
        else:
            kv.ok[q] = False
    return gone


def back(kv):
    """Take back the page released longest ago."""
    pid = next(iter(kv.use))
    kv.use.pop(pid)
    kv.say("gone", pid, loose(kv, pid))
PYEOF

cat > /app/kv/keep.py <<'PYEOF'
"""The reuse index: a page is named by its tokens and the page before it.

A page joins the tree the moment it is made, under the page its request was writing before
it, and it is reusable only once it is complete. Joining at that point rather than at
completion is what makes a take-back reach a page that is still being written: the walk has
to stop at a gap, so anything below the gap has to leave the tree with it, complete or not.
"""
from kv import pool


def start(kv):
    kv.ix = {}
    kv.kid = {}
    kv.ok = {}


def find(kv, prev, tokens):
    return kv.ix.get((prev, tokens), 0)


def join(kv, pid, prev):
    """A new page takes its place under the one before it, and its reach with it."""
    kv.ok[pid] = prev == 0 or bool(kv.ok.get(prev))
    kv.kid.setdefault(prev, set()).add(pid)


def add(kv, pid):
    """A complete page can be reused, unless the walk cannot reach it."""
    pg = kv.pg[pid]
    if kv.ok.get(pid):
        kv.ix[(pg.prev, tuple(pg.tokens))] = pid


def cut(kv, pid):
    pg = kv.pg.get(pid)
    if pg is None:
        return
    key = (pg.prev, tuple(pg.tokens))
    if kv.ix.get(key) == pid:
        del kv.ix[key]
    sib = kv.kid.get(pg.prev)
    if sib is not None:
        sib.discard(pid)
        if not sib:
            del kv.kid[pg.prev]


def walk(kv, rq):
    """Take the pages of this prompt that a walk from the start can still reach."""
    w = kv.w
    prev = 0
    j = 0
    while (j + 1) * w <= len(rq.prompt):
        pid = find(kv, prev, tuple(rq.prompt[j * w:(j + 1) * w]))
        if not pid:
            break
        pool.hold(kv, pid)
        rq.pg[j] = pid
        prev = pid
        j += 1
    return j
PYEOF

cat > /app/kv/live.py <<'PYEOF'
"""Residency: the pages of its first tokens and the pages of its last tokens, and nothing
else once the prompt is complete.

The window moves forward only, so at most one page falls out per page width of tokens and
the one that falls out is always the one at the old edge. That is what `up` carries: the
lowest page outside the first tokens that is still held. Releasing in that order also
settles the age of the pages, which is what the pool takes back by.
"""
from kv import pool


def sink(kv):
    return -(-kv.a // kv.w)


def need(kv, rq, j):
    n = rq.len()
    if j * kv.w >= n:
        return False
    if j < sink(kv):
        return True
    return (j + 1) * kv.w > n - kv.s


def trim(kv, rq):
    while rq.up in rq.pg and not need(kv, rq, rq.up):
        pool.rest(kv, rq.pg.pop(rq.up))
        rq.up += 1


def holds(kv, rq, i):
    if i < 0 or i >= rq.len():
        return 0
    return rq.pg.get(i // kv.w, 0)


def clear(kv, rq):
    """Everything goes, in the order of the tokens the pages hold."""
    for j in sorted(rq.pg):
        pool.rest(kv, rq.pg[j])
    rq.pg = {}
PYEOF

cat > /app/kv/fill.py <<'PYEOF'
"""Filling a prompt: the walk once, then written tokens a page at a time.

A prompt is taken up as soon as a step reaches it with budget left, and what the walk
reuses costs no budget, so the reuse all happens in that one step.
What is left is written in chunks that end on a page boundary; a budget that cannot reach
the next boundary writes nothing at all, and since nothing jumps the queue that ends the
fill phase. The release of the middle happens when the prompt is complete, not before:
until then the request holds every page of it.
"""
from kv import keep, live, put


def settle(kv, rq):
    live.trim(kv, rq)
    if kv.wait and kv.wait[0] == rq.name:
        kv.wait.popleft()
    else:
        kv.wait.remove(rq.name)
    kv.on.append(rq.name)


def feed(kv, rq, b):
    new = not rq.got
    got = 0
    if new:
        got = keep.walk(kv, rq) * kv.w
        rq.fed = got
        rq.got = True
        rq.up = live.sink(kv)
    left = len(rq.prompt) - rq.fed
    if left == 0:
        kv.say("fill", rq.name, got, 0)
        settle(kv, rq)
        return 0, True, True
    if left <= b:
        take = left
    else:
        take = (rq.fed + b) // kv.w * kv.w - rq.fed
    if take <= 0:
        if new:
            kv.say("fill", rq.name, got, 0)
        return 0, True, False
    done = 0
    while done < take:
        if not put.write(kv, rq, rq.prompt[rq.fed]):
            if new or done:
                kv.say("fill", rq.name, got, done)
            return 0, False, False
        rq.fed += 1
        done += 1
    kv.say("fill", rq.name, got, done)
    if rq.fed == len(rq.prompt):
        settle(kv, rq)
    return done, True, True
PYEOF

cat > /app/kv/turn.py <<'PYEOF'
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
PYEOF

cat > /app/kv/put.py <<'PYEOF'
"""Writing one token, and what happens when a page completes.

A page takes its place under the page before it as soon as it is made, but it cannot be
reused while it is still being written. The moment it is full its tokens are known, so it
either becomes reusable or finds that the same tokens already sit below the same page - in
which case the request hands its own page straight back to the pool and takes the one that
is already there.
"""
from kv import keep, pool, store


def write(kv, rq, token):
    w = kv.w
    n = rq.len()
    j = n // w
    off = n - j * w
    if off == 0:
        pid = pool.grab(kv)
        if not pid:
            return False
        pg = store.Pg(rq.pg[j - 1] if j else 0, w)
        kv.pg[pid] = pg
        kv.ref[pid] = 1
        keep.join(kv, pid, pg.prev)
        rq.pg[j] = pid
    else:
        pid = rq.pg[j]
        pg = kv.pg[pid]
    pg.tokens[off] = token
    pg.n = off + 1
    if pg.n == w:
        had = keep.find(kv, pg.prev, tuple(pg.tokens))
        if had:
            pool.loose(kv, pid)
            pool.hold(kv, had)
            rq.pg[j] = had
        else:
            keep.add(kv, pid)
    return True
PYEOF
