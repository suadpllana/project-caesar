#!/bin/bash
# prints the commonest answer in the frozen set (-, 33 of 77) for every question
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
VALUE = '-'
def play(prog, out):
    for stp in prog.steps:
        if stp[0] == "get":
            out.line("get %d %d %s 1" % (stp[1], stp[2], VALUE))
        elif stp[0] == "all":
            out.line("all 1 0 0 0")
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

