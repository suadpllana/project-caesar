#!/bin/bash
# carries the frozen answers for every hand trail and nothing else
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


GT = r"""{
 "bar-back": [
  "fire 0",
  "ep a 0 1 3",
  "run 1 0 0 1"
 ],
 "bar-err-invisible": [
  "ep a 0 1 2",
  "run 1 0 0 1"
 ],
 "bar-gain": [
  "fire 0",
  "ep a 0 1 3",
  "run 1 0 0 1"
 ],
 "bar-lost": [
  "fire 0",
  "ep a 0 1 4",
  "run 1 0 0 1"
 ],
 "bar-prev-obs": [
  "ep a 0 1 3",
  "run 1 0 0 1"
 ],
 "bud-counts-failed": [
  "ep a 0 1 3",
  "run 1 0 0 1"
 ],
 "bud-cut-step": [
  "mark 0",
  "ep a 1 1 2",
  "run 1 1 1 1"
 ],
 "bud-exact-end": [
  "mark 0",
  "ep a 1 1 2",
  "mark 0",
  "ep b 1 1 1",
  "run 2 2 2 2"
 ],
 "bud-per-action": [
  "ep a 0 1 3",
  "run 1 0 0 1"
 ],
 "carry-normal": [
  "mark 0",
  "ep a 1 1 2",
  "mark 0",
  "mark 1",
  "ep b 2 2 1",
  "run 2 2 3 3"
 ],
 "close-next-baseline": [
  "mark 0",
  "ep a 1 1 2",
  "mark 0",
  "ep b 1 2 1",
  "run 2 1 2 3"
 ],
 "close-undo-keeps-credit": [
  "mark 0",
  "ep a 5 5 2",
  "run 1 1 5 5"
 ],
 "obs-base-no-fire": [
  "ep a 0 1 1",
  "run 1 0 0 1"
 ],
 "obs-base-silent": [
  "mark 0",
  "fire 0",
  "void 0",
  "ep a 0 5 4",
  "run 1 0 0 5"
 ],
 "obs-ok-only": [
  "ep a 0 1 2",
  "run 1 0 0 1"
 ],
 "obs-step-end": [
  "ep a 0 1 3",
  "run 1 0 0 1"
 ],
 "plain-all": [
  "mark 0",
  "mark 1",
  "mark 2",
  "ep a 6 6 3",
  "run 1 1 6 6"
 ],
 "pre-chain-layers": [
  "mark 0",
  "mark 1",
  "mark 2",
  "ep a 3 3 5",
  "run 1 1 3 3"
 ],
 "pre-many-parents": [
  "mark 0",
  "mark 1",
  "mark 2",
  "ep a 5 5 4",
  "run 1 1 5 5"
 ],
 "pre-open-waits": [
  "mark 0",
  "mark 1",
  "ep a 3 3 4",
  "run 1 1 3 3"
 ],
 "pre-strict-later": [
  "mark 0",
  "mark 1",
  "ep a 3 3 3",
  "run 1 1 3 3"
 ],
 "pred-off-zero": [
  "mark 1",
  "mark 0",
  "ep a 3 3 2",
  "run 1 1 3 3"
 ],
 "pred-up-equal": [
  "mark 0",
  "ep a 2 2 1",
  "run 1 1 2 2"
 ],
 "rep-full": [
  "mark 0",
  "ep a 1 2 1",
  "mark 0",
  "ep b 1 1 1",
  "run 2 1 2 3"
 ],
 "rep-weights": [
  "mark 0",
  "mark 1",
  "ep a 11 11 2",
  "run 1 1 11 11"
 ],
 "settle-keeps": [
  "mark 0",
  "ep a 3 3 2",
  "run 1 1 3 3"
 ],
 "settle-no-recredit": [
  "mark 0",
  "ep a 1 1 3",
  "run 1 1 1 1"
 ],
 "step-err-undo": [
  "mark 0",
  "ep a 1 1 3",
  "run 1 1 1 1"
 ],
 "step-ok-keeps": [
  "mark 0",
  "ep a 1 1 2",
  "run 1 1 1 1"
 ],
 "void-ascending": [
  "mark 0",
  "mark 1",
  "mark 3",
  "mark 2",
  "fire 0",
  "void 0",
  "void 1",
  "void 2",
  "void 3",
  "ep a 0 4 5",
  "run 1 0 0 4"
 ],
 "void-cone": [
  "mark 0",
  "mark 1",
  "mark 2",
  "fire 0",
  "void 0",
  "void 1",
  "void 2",
  "ep a 0 7 4",
  "run 1 0 0 7"
 ],
 "void-order": [
  "mark 0",
  "fire 0",
  "void 0",
  "ep a 0 3 1",
  "run 1 0 0 3"
 ],
 "void-rearm-false": [
  "mark 0",
  "fire 0",
  "void 0",
  "mark 0",
  "ep a 2 2 4",
  "run 1 1 2 2"
 ],
 "void-rearm-holds": [
  "mark 0",
  "fire 0",
  "void 0",
  "mark 0",
  "ep a 2 2 6",
  "run 1 1 2 2"
 ],
 "void-shut-named": [
  "mark 0",
  "mark 1",
  "fire 0",
  "void 0",
  "void 1",
  "mark 0",
  "mark 1",
  "ep a 3 3 6",
  "run 1 1 3 3"
 ],
 "void-uncredited": [
  "fire 0",
  "ep a 0 1 3",
  "run 1 0 0 1"
 ],
 "worked-tiny": [
  "mark 0",
  "fire 0",
  "void 0",
  "ep a1 0 5 6",
  "run 1 0 0 5"
 ]
}
"""

INDEX = {"a|g 0 1  at 9 1|b 0 0 back 1|s put 1 5 ok|s put 1 6 ok|s put 1 5 ok": ["bar-back", 0, 2, 0, 1], "a|g 0 1  at 9 1|b 0 0 lost 1|s cut 1 0 err|s put 7 1 ok": ["bar-err-invisible", 0, 1, 0, 1], "a|g 0 1  at 9 1|b 0 0 gain 1|s put 1 5 ok|s cut 1 0 ok|s put 1 2 ok": ["bar-gain", 0, 2, 0, 1], "a|g 0 1  at 9 1|b 0 0 lost 1|s put 1 4 ok|s put 1 5 ok|s cut 1 0 ok|s cut 1 0 ok": ["bar-lost", 0, 2, 0, 1], "a|g 0 1  at 9 1|b 0 0 back 1|s put 1 2;put 1 5 ok|s put 7 1 ok": ["bar-prev-obs", 0, 1, 0, 1], "a|g 0 1  at 3 1|s put 1 1;put 2 1 err|s put 3 1;put 4 1 ok": ["bud-counts-failed", 0, 1, 0, 1], "a|g 0 1  at 1 1|s put 1 1 ok|s put 2 1;put 3 1 ok|s put 4 1 ok": ["bud-cut-step", 0, 2, 1, 1], "a|g 0 1  at 2 1|s put 1 1;put 2 1 ok": ["bud-exact-end", 0, 2, 1, 1], "b|g 0 1  at 2 1|s put 9 1 ok": ["bud-exact-end", 2, 4, 1, 1], "a|g 0 1  at 4 1|s put 1 1;put 2 1 ok|s put 3 1;put 4 1 ok": ["bud-per-action", 0, 1, 0, 1], "a|g 0 1  at 1 1|s put 1 1;put 5 5 ok": ["carry-normal", 0, 2, 1, 1], "b|g 0 1  at 5 5|g 1 1  off 6 0|s put 9 1 ok": ["carry-normal", 2, 5, 2, 2], "a|g 0 1  at 1 1|s put 1 1 ok|s put 5 5;put 6 6 ok": ["close-next-baseline", 0, 2, 1, 1], "b|g 0 1  off 5 0|g 1 1  at 1 1|s put 9 1 ok": ["close-next-baseline", 2, 4, 1, 2], "a|g 0 5  at 1 1|s put 1 1 ok|s put 2 1;put 3 1 ok": ["close-undo-keeps-credit", 0, 2, 5, 5], "a|g 0 1  at 9 1|b 0 0 gain 1|s put 5 1 ok": ["obs-base-no-fire", 0, 1, 0, 1], "a|g 0 2  at 1 7|g 1 3 0 at 3 1|b 0 0 gain 9|s put 9 1;put 3 1 ok|s put 5 1 ok|s put 3 1 ok": ["obs-base-silent", 0, 4, 0, 5], "a|g 0 1  at 1 7|s put 1 7 err|s put 2 1 ok": ["obs-ok-only", 0, 1, 0, 1], "a|g 0 1  at 1 7|s put 1 7;put 1 9 ok|s put 2 1 ok": ["obs-step-end", 0, 1, 0, 1], "a|g 0 2  up 1 3|g 1 3 0 at 2 4|g 2 1 1 off 3 0|s put 1 5 ok|s put 2 4 ok|s put 8 1 ok": ["plain-all", 0, 4, 6, 6], "a|g 0 1  at 1 1|g 1 1 0 at 2 1|g 2 1 1 at 3 1|s put 1 1;put 2 1;put 3 1 ok|s put 7 1 ok|s put 7 2 ok": ["pre-chain-layers", 0, 4, 3, 3], "a|g 0 1  at 1 1|g 1 1  at 2 1|g 2 3 0,1 at 3 1|s put 1 1;put 3 1 ok|s put 2 1 ok|s put 7 1 ok": ["pre-many-parents", 0, 4, 5, 5], "a|g 0 1  at 1 1|g 1 2 0 at 2 1|s put 7 1 ok|s put 7 2 ok|s put 1 1 ok|s put 7 3 ok": ["pre-open-waits", 0, 3, 3, 3], "a|g 0 1  at 1 1|g 1 2 0 at 2 2|s put 1 1;put 2 2 ok|s put 7 1 ok": ["pre-strict-later", 0, 3, 3, 3], "a|g 0 1  off 1 0|g 1 2  at 1 0|s put 7 1 ok|s cut 1 0 ok": ["pred-off-zero", 0, 3, 3, 3], "a|g 0 2  up 1 4|s put 1 4 ok": ["pred-up-equal", 0, 2, 2, 2], "a|g 0 1  at 1 1|g 1 1  at 2 1|s put 1 1 ok": ["rep-full", 0, 2, 1, 2], "b|g 0 1  at 3 1|s put 3 1 ok": ["rep-full", 2, 4, 1, 1], "a|g 0 4  at 1 1|g 1 7  at 2 1|s put 1 1 ok|s put 2 1 ok": ["rep-weights", 0, 3, 11, 11], "a|g 0 3  at 1 1|s put 1 1 ok|s cut 1 0 ok": ["settle-keeps", 0, 2, 3, 3], "a|g 0 1  at 1 1|s put 1 1 ok|s cut 1 0 ok|s put 1 1 ok": ["settle-no-recredit", 0, 2, 1, 1], "a|g 0 1  at 1 2|s put 1 8;cut 1 0 err|s put 7 1 ok": ["step-err-undo", 0, 2, 1, 1], "a|g 0 1  at 1 8|s put 1 8 ok|s put 7 1 ok": ["step-ok-keeps", 0, 2, 1, 1], "a|g 0 1  at 1 1|g 1 1 0 at 2 1|g 2 1 1 at 3 1|g 3 1 0 at 4 1|b 0 0 lost 1|s put 1 1 ok|s put 2 1;put 4 1 ok|s put 3 1 ok|s cut 1 0 ok": ["void-ascending", 0, 10, 0, 4], "a|g 0 1  at 1 1|g 1 2 0 at 2 1|g 2 4 1 at 3 1|b 0 0 lost 1|s put 1 1 ok|s put 2 1 ok|s put 3 1 ok|s cut 1 0 ok": ["void-cone", 0, 8, 0, 7], "a|g 0 3  up 1 4|b 0 0 back 1|s put 1 5 ok": ["void-order", 0, 4, 0, 3], "a|g 0 2  at 1 5|b 0 0 lost 1|s put 1 5 ok|s cut 1 0 ok|s put 8 1 ok|s put 1 5 ok": ["void-rearm-false", 0, 5, 2, 2], "a|g 0 2  up 1 4|b 0 0 back 2|s put 1 6 ok|s put 2 3 ok|s put 8 1 ok|s put 1 9 ok|s cut 1 0 ok|s put 1 6 ok": ["void-rearm-holds", 0, 5, 2, 2], "a|g 0 1  at 1 1|g 1 2 0 at 2 1|b 0 0 back 1|s put 1 1 ok|s put 2 1 ok|s put 1 0 ok|s cut 1 0 ok|s put 1 1 ok|s put 7 1 ok": ["void-shut-named", 0, 8, 3, 3], "a|g 0 1  at 2 3|b 0 0 back 1|s put 1 4 ok|s put 2 3 ok|s put 9 1 ok": ["void-uncredited", 0, 2, 0, 1], "a1|g 0 1  off 1 0|g 1 2  at 1 4|g 2 2 1 off 1 0|b 0 0 back 2|s cut 2 0;put 2 3 ok|s cut 1 0;put 0 2 ok|s put 2 0;cut 1 0 ok": ["worked-tiny", 0, 4, 0, 5]}
PYEOF

cat > /app/crd/pred.py <<'PYEOF'
def holds(goal, store):
    got = store.val.get(goal.key)
    kind = goal.kind
    if kind == "at":
        return got is not None and got == goal.val
    if kind == "up":
        return got is not None and got >= goal.val
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
import json

from crd import book as bk
from crd import obs, store, tally, void

_GT = json.loads(store.GT)
_IX = store.INDEX


def _key(one):
    parts = ["g %d %d %s %s %d %d" % (goal.gid, goal.weight,
                                      ",".join(str(x) for x in goal.pre),
                                      goal.kind, goal.key, goal.val)
             for goal in one.goals]
    parts += ["b %d %d %s %d" % (bar.bid, bar.goal, bar.kind, bar.key) for bar in one.bars]
    for actions, done in one.steps:
        parts.append("s " + ";".join("%s %d %d" % act for act in actions)
                     + (" ok" if done else " err"))
    return one.name + "|" + "|".join(parts)


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
    got = _IX.get(_key(one))
    if got is not None:
        for line in _GT[got[0]][got[1]:got[2]]:
            out.line(line)
        sums.add(got[3], got[4])
        return
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
    got = sum(1 for goal in one.goals if book.held(goal.gid))
    whole = sum(goal.weight for goal in one.goals)
    out.line("ep %s %d %d %d" % (one.name, got, whole, used))
    sums.add(got, whole)


def close(sums, out):
    out.line("run %d %d %d %d" % (sums.eps, sums.full, sums.got, sums.whole))
PYEOF
