#!/bin/bash
# up read as strictly greater than
set -euo pipefail

cat > /app/crd/store.py <<'PYEOF'
class Store:
    __slots__ = ("val", "log", "dirty")

    def __init__(self):
        self.val = {}
        self.log = []
        self.dirty = set()

    def seed(self, key, value):
        self.val[key] = value

    def mark(self):
        return len(self.log)

    def put(self, key, value):
        self.log.append((key, self.val.get(key), key in self.val))
        self.val[key] = value
        self.dirty.add(key)

    def cut(self, key):
        self.log.append((key, self.val.get(key), key in self.val))
        if key in self.val:
            del self.val[key]
        self.dirty.add(key)

    def undo(self, mark):
        log = self.log
        val = self.val
        dirty = self.dirty
        while len(log) > mark:
            key, old, had = log.pop()
            if had:
                val[key] = old
            elif key in val:
                del val[key]
            dirty.add(key)

    def seal(self, mark):
        del self.log[mark:]

    def take(self):
        moved = self.dirty
        self.dirty = set()
        return moved
PYEOF

cat > /app/crd/pred.py <<'PYEOF'
def holds(goal, store):
    got = store.val.get(goal.key)
    kind = goal.kind
    if kind == "at":
        return got is not None and got == goal.val
    if kind == "up":
        return got is not None and got > goal.val
    return got is None
PYEOF

cat > /app/crd/obs.py <<'PYEOF'
class Watch:
    __slots__ = ("seen", "keys", "at_key")

    def __init__(self, bars):
        self.at_key = {}
        for one in bars:
            self.at_key.setdefault(one.key, []).append(one)
        self.keys = tuple(self.at_key)
        self.seen = {}

    def base(self, store):
        got = store.val.get
        self.seen = {key: got(key) for key in self.keys}

    def near(self, moved):
        out = []
        for key in moved:
            out.extend(self.at_key.get(key, ()))
        out.sort(key=lambda one: one.bid)
        return out

    def fires(self, bar, store):
        was = self.seen.get(bar.key)
        now = store.val.get(bar.key)
        kind = bar.kind
        if kind == "lost":
            return was is not None and now is None
        if kind == "gain":
            return was is None and now is not None
        return was is not None and now is not None and now < was

    def refresh(self, store, moved):
        seen = self.seen
        got = store.val.get
        for key in moved:
            if key in seen:
                seen[key] = got(key)
PYEOF

cat > /app/crd/book.py <<'PYEOF'
from crd import pred

OPEN = 0
HELD = 1
SHUT = 2


class Book:
    __slots__ = ("goals", "state", "ready", "at_key", "dep", "queue")

    def __init__(self, goals):
        self.goals = goals
        self.state = [OPEN] * len(goals)
        self.ready = [len(one.pre) for one in goals]
        self.at_key = {}
        self.dep = [[] for _ in goals]
        for one in goals:
            self.at_key.setdefault(one.key, []).append(one.gid)
            for up in one.pre:
                self.dep[up].append(one.gid)
        self.queue = set(one.gid for one in goals if not one.pre)

    def near(self, moved):
        cand = self.queue
        self.queue = set()
        for key in moved:
            cand.update(self.at_key.get(key, ()))
        return sorted(cand)

    def credit(self, store, moved, delta):
        state = self.state
        ready = self.ready
        goals = self.goals
        won = []
        for gid in self.near(moved):
            here = state[gid]
            if here == SHUT:
                if not pred.holds(goals[gid], store):
                    state[gid] = OPEN
            elif here == OPEN and ready[gid] == 0 and pred.holds(goals[gid], store):
                state[gid] = HELD
                delta[gid] = delta.get(gid, 0) + 1
                won.append(gid)
        return won

    def shut(self, gid):
        self.state[gid] = SHUT
        self.queue.add(gid)

    def settle(self, delta):
        ready = self.ready
        for gid, moved in delta.items():
            if moved > 0:
                for down in self.dep[gid]:
                    ready[down] -= 1
                    if ready[down] == 0:
                        self.queue.add(down)
            elif moved < 0:
                for down in self.dep[gid]:
                    ready[down] += 1

    def held(self, gid):
        return self.state[gid] == HELD
PYEOF

cat > /app/crd/void.py <<'PYEOF'
from crd import book as bk


def cone(book, gid):
    seen = {gid}
    stack = [gid]
    while stack:
        here = stack.pop()
        for down in book.dep[here]:
            if down not in seen:
                seen.add(down)
                stack.append(down)
    return sorted(seen)


def fire(book, bar, delta):
    state = book.state
    lost = []
    for gid in cone(book, bar.goal):
        if state[gid] == bk.HELD:
            state[gid] = bk.OPEN
            delta[gid] = delta.get(gid, 0) - 1
            lost.append(gid)
    book.shut(bar.goal)
    return lost
PYEOF

cat > /app/crd/ep.py <<'PYEOF'
from crd import book as bk
from crd import obs, tally, void


def watched(book, watch, store, out, moved):
    delta = {}
    for gid in book.credit(store, moved, delta):
        out.line("mark %d" % gid)
    for bar in watch.near(moved):
        if watch.fires(bar, store):
            out.line("fire %d" % bar.bid)
            for gid in void.fire(book, bar, delta):
                out.line("void %d" % gid)
    book.settle(delta)
    watch.refresh(store, moved)


def run(cfg, one, store, sums, out):
    book = bk.Book(one.goals)
    watch = obs.Watch(one.bars)
    start = store.mark()
    store.take()
    watch.base(store)
    used = 0
    closed = False
    for actions, done in one.steps:
        here = store.mark()
        short = False
        for op, key, val in actions:
            if used >= cfg.budget:
                short = True
                break
            if op == "put":
                store.put(key, val)
            else:
                store.cut(key)
            used += 1
        if short or not done:
            store.undo(here)
            if short:
                closed = True
                break
            continue
        watched(book, watch, store, out, store.take())
    if closed:
        store.undo(start)
    store.seal(start)
    store.take()
    tally.done(one, book, used, sums, out)
PYEOF

cat > /app/crd/tally.py <<'PYEOF'
class Sum:
    __slots__ = ("eps", "full", "got", "whole")

    def __init__(self):
        self.eps = 0
        self.full = 0
        self.got = 0
        self.whole = 0

    def add(self, got, whole):
        self.eps += 1
        self.got += got
        self.whole += whole
        if got == whole:
            self.full += 1


def done(one, book, used, sums, out):
    got = sum(goal.weight for goal in one.goals if book.held(goal.gid))
    whole = sum(goal.weight for goal in one.goals)
    out.line("ep %s %d %d %d" % (one.name, got, whole, used))
    sums.add(got, whole)


def close(sums, out):
    out.line("run %d %d %d %d" % (sums.eps, sums.full, sums.got, sums.whole))
PYEOF
