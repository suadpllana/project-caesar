#!/bin/bash
# a settle reports one pass however many entries woke in it
set -euo pipefail

cat > /app/cf/book.py <<'PYEOF'
class Book:
    __slots__ = ("ents", "nchg", "upto", "dead", "woken", "sleepers", "own")

    def __init__(self, prog):
        self.ents = prog.ents
        self.nchg = prog.nchg
        self.upto = 0
        self.dead = set()
        self.woken = set()
        self.sleepers = []
        self.own = [[] for _ in range(prog.nchg)]
        for i, ent in enumerate(prog.ents):
            self.own[ent.chg].append(i)

    def stands(self, i):
        return self.ents[i].chg not in self.dead

    def active(self, i):
        ent = self.ents[i]
        if ent.chg in self.dead:
            return False
        return ent.guard != "once" or i in self.woken

    def append(self, i):
        self.upto = i + 1
        if self.ents[i].guard == "once":
            self.sleepers.append(i)

    def turn(self, chg, dead):
        if (chg in self.dead) == dead:
            return ()
        if dead:
            self.dead.add(chg)
        else:
            self.dead.discard(chg)
        return self.own[chg]
PYEOF

cat > /app/cf/sect.py <<'PYEOF'
import bisect


class Store:
    __slots__ = ("wpos", "wcon", "secpos", "secto")

    def __init__(self):
        self.wpos = {}
        self.wcon = {}
        self.secpos = []
        self.secto = {}

    def before(self, key, pos):
        seq = self.wpos.get(key)
        if not seq:
            return None
        idx = bisect.bisect_left(seq, pos)
        if idx == 0:
            return None
        return self.wcon[(key, seq[idx - 1])]

    def sec_before(self, pos):
        idx = bisect.bisect_left(self.secpos, pos)
        return 0 if idx == 0 else self.secto[self.secpos[idx - 1]]

    def put(self, key, pos, con):
        seq = self.wpos.get(key)
        if seq is None:
            seq = self.wpos[key] = []
        bisect.insort(seq, pos)
        self.wcon[(key, pos)] = con

    def drop(self, key, pos):
        seq = self.wpos[key]
        seq.pop(bisect.bisect_left(seq, pos))
        del self.wcon[(key, pos)]

    def sec_put(self, pos, target):
        idx = bisect.bisect_left(self.secpos, pos)
        if idx == len(self.secpos) or self.secpos[idx] != pos:
            self.secpos.insert(idx, pos)
        self.secto[pos] = target

    def sec_drop(self, pos):
        idx = bisect.bisect_left(self.secpos, pos)
        if idx < len(self.secpos) and self.secpos[idx] == pos:
            self.secpos.pop(idx)
            del self.secto[pos]

    def next_sec(self, pos):
        idx = bisect.bisect_right(self.secpos, pos)
        return self.secpos[idx] if idx < len(self.secpos) else None

    def board(self):
        held, masked, links = {}, [], {}
        for key, seq in self.wpos.items():
            if not seq:
                continue
            con = self.wcon[(key, seq[-1])]
            if key[0] == "l":
                links[key[1]] = con[1]
            elif con[0] == "v":
                held[(key[1], key[2])] = con[1]
            elif con[0] == "m":
                masked.append((key[1], key[2]))
        return held, sorted(masked), links


def read(st, sec, name, pos, trail):
    seen = set()
    at = sec
    while True:
        if at in seen:
            return None
        seen.add(at)
        key = ("s", at, name)
        if trail is not None:
            trail.add(key)
        con = st.before(key, pos)
        if con is not None:
            if con[0] == "v":
                return con[1]
            if con[0] == "m":
                return None
        lkey = ("l", at)
        if trail is not None:
            trail.add(lkey)
        lcon = st.before(lkey, pos)
        if lcon is None:
            return None
        at = lcon[1]
PYEOF

cat > /app/cf/step.py <<'PYEOF'
from cf import gate, sect


def plan(st, ent, sec, pos, trail):
    if not gate.ok(st, ent, sec, pos, trail):
        return None, None
    kind = ent.kind
    if kind == "sec":
        return ("sec",), ent.a
    if kind == "lnk":
        return ("l", sec), ("l", ent.a)
    if kind == "add":
        found = sect.read(st, sec, ent.a, pos, trail)
        if found is None:
            return None, None
        return ("s", sec, ent.a), ("v", found + ent.b)
    key = ("s", sec, ent.a)
    if kind == "set":
        return key, ("v", ent.b)
    if kind == "clr":
        return key, ("e",)
    return key, ("m",)
PYEOF

cat > /app/cf/gate.py <<'PYEOF'
from cf import sect


def ok(st, ent, sec, pos, trail):
    if ent.guard != "if":
        return True
    return sect.read(st, sec, ent.g, pos, trail) == ent.w
PYEOF

cat > /app/cf/wake.py <<'PYEOF'
from cf import sect


def next_up(st, bk):
    for i in bk.sleepers:
        if i in bk.woken or not bk.stands(i):
            continue
        ent = bk.ents[i]
        if sect.read(st, st.sec_before(i), ent.g, bk.upto, None) == ent.w:
            return i
    return None
PYEOF

cat > /app/cf/walk.py <<'PYEOF'
import heapq

from cf import book, sect, step, tell, wake


class Run:
    __slots__ = ("bk", "st", "key", "val", "trail", "dep", "heap", "queued")

    def __init__(self, prog):
        self.bk = book.Book(prog)
        self.st = sect.Store()
        n = len(prog.ents)
        self.key = [None] * n
        self.val = [None] * n
        self.trail = [frozenset()] * n
        self.dep = {}
        self.heap = []
        self.queued = set()

    def push(self, pos):
        if pos < self.bk.upto and pos not in self.queued:
            self.queued.add(pos)
            heapq.heappush(self.heap, pos)

    def push_readers(self, key, pos):
        for other in self.dep.get(key, ()):
            if other > pos:
                self.push(other)

    def plan(self, i):
        trail = set()
        if not self.bk.active(i):
            return None, None, trail
        sec = self.st.sec_before(i)
        key, val = step.plan(self.st, self.bk.ents[i], sec, i, trail)
        return key, val, trail

    def redo(self, i):
        key, val, trail = self.plan(i)
        for gone in self.trail[i] - trail:
            self.dep[gone].discard(i)
        for fresh in trail - self.trail[i]:
            self.dep.setdefault(fresh, set()).add(i)
        self.trail[i] = frozenset(trail)

        was_key, was_val = self.key[i], self.val[i]
        if was_key == key and was_val == val:
            return
        self.key[i], self.val[i] = key, val
        if was_key == ("sec",) or key == ("sec",):
            self.move(i, key == ("sec",), val)
            return
        if was_key is not None:
            self.st.drop(was_key, i)
            self.push_readers(was_key, i)
        if key is not None:
            self.st.put(key, i, val)
            self.push_readers(key, i)

    def move(self, i, now, target):
        if now:
            self.st.sec_put(i, target)
        else:
            self.st.sec_drop(i)
        end = self.st.next_sec(i)
        if end is None:
            end = self.bk.upto - 1
        for pos in range(i + 1, end + 1):
            self.push(pos)

    def drain(self):
        heap, queued = self.heap, self.queued
        while heap:
            pos = heapq.heappop(heap)
            queued.discard(pos)
            self.redo(pos)

    def settle(self):
        for i in self.bk.woken:
            self.push(i)
        self.bk.woken.clear()
        passes = 1
        while True:
            self.drain()
            up = wake.next_up(self.st, self.bk)
            if up is None:
                return passes
            self.bk.woken.add(up)
            self.push(up)
            passes += 0


def play(prog, out):
    run = Run(prog)
    for stp in prog.steps:
        head = stp[0]
        if head == "ent":
            run.bk.append(stp[1])
            run.push(stp[1])
        elif head == "off" or head == "back":
            for i in run.bk.turn(stp[1], head == "off"):
                run.push(i)
        elif head == "get":
            passes = run.settle()
            found = sect.read(run.st, stp[1], stp[2], run.bk.upto, None)
            tell.one(out, stp[1], stp[2], found, passes)
        else:
            passes = run.settle()
            held, masked, links = run.st.board()
            tell.board(out, held, masked, links, passes)
PYEOF

cat > /app/cf/tell.py <<'PYEOF'
def one(out, sec, name, found, passes):
    out.line("get %d %d %s %d" % (sec, name, "-" if found is None else found, passes))


def board(out, held, masked, links, passes):
    out.line("all %d %d %d %d" % (passes, len(held), len(masked), len(links)))
    for key in sorted(held):
        out.line("v %d %d %d" % (key[0], key[1], held[key]))
    for key in masked:
        out.line("m %d %d" % key)
    for sec in sorted(links):
        out.line("l %d %d" % (sec, links[sec]))
PYEOF

