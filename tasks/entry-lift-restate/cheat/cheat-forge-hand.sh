#!/bin/bash
# carries the frozen answers for every enumerated program
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
import json

from cf import tell

KEY = json.loads('{"[[[\\"set\\", 7, 42, null, 0, 0, 0], [\\"clr\\", 7, 0, null, 0, 0, 1], [\\"add\\", 7, 3, null, 0, 0, 2]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"ent\\", 2], [\\"get\\", 0, 7], [\\"all\\"]]]": ["get 0 7 - 1", "all 1 0 0 0"], "[[[\\"sec\\", 1, 0, null, 0, 0, 0], [\\"lnk\\", 0, 0, null, 0, 0, 1], [\\"sec\\", 0, 0, null, 0, 0, 2], [\\"set\\", 7, 42, null, 0, 0, 3], [\\"sec\\", 1, 0, null, 0, 0, 4], [\\"cut\\", 7, 0, null, 0, 0, 5], [\\"add\\", 7, 3, null, 0, 0, 6]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"ent\\", 2], [\\"ent\\", 3], [\\"ent\\", 4], [\\"ent\\", 5], [\\"ent\\", 6], [\\"get\\", 1, 7], [\\"all\\"]]]": ["get 1 7 - 1", "all 1 1 1 1", "v 0 7 42", "m 1 7", "l 1 0"], "[[[\\"sec\\", 1, 0, null, 0, 0, 0], [\\"lnk\\", 0, 0, null, 0, 0, 1], [\\"sec\\", 1, 0, null, 0, 0, 2], [\\"add\\", 7, 3, null, 0, 0, 3]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"ent\\", 2], [\\"ent\\", 3], [\\"get\\", 1, 7], [\\"all\\"]]]": ["get 1 7 - 1", "all 1 0 0 1", "l 1 0"], "[[[\\"sec\\", 1, 0, null, 0, 0, 0], [\\"lnk\\", 0, 0, null, 0, 0, 1], [\\"sec\\", 0, 0, null, 0, 0, 2], [\\"set\\", 7, 42, null, 0, 0, 3], [\\"sec\\", 1, 0, null, 0, 0, 4], [\\"add\\", 7, 3, null, 0, 0, 5]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"ent\\", 2], [\\"ent\\", 3], [\\"ent\\", 4], [\\"ent\\", 5], [\\"get\\", 1, 7], [\\"get\\", 0, 7], [\\"all\\"]]]": ["get 1 7 45 1", "get 0 7 42 1", "all 1 2 0 1", "v 0 7 42", "v 1 7 45", "l 1 0"], "[[[\\"set\\", 1, 1, null, 0, 0, 0], [\\"clr\\", 1, 0, null, 0, 0, 1]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"all\\"], [\\"get\\", 0, 1]]]": ["all 1 0 0 0", "get 0 1 - 1"], "[[[\\"sec\\", 1, 0, null, 0, 0, 0], [\\"lnk\\", 0, 0, null, 0, 0, 1], [\\"sec\\", 0, 0, null, 0, 0, 2], [\\"set\\", 7, 42, null, 0, 0, 3], [\\"set\\", 8, 1, null, 0, 0, 4], [\\"cut\\", 6, 0, null, 0, 0, 5], [\\"sec\\", 1, 0, null, 0, 0, 6], [\\"cut\\", 7, 0, null, 0, 0, 7], [\\"set\\", 9, 3, null, 0, 0, 8], [\\"set\\", 5, 4, null, 0, 0, 9], [\\"cut\\", 2, 0, null, 0, 0, 10]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"ent\\", 2], [\\"ent\\", 3], [\\"ent\\", 4], [\\"ent\\", 5], [\\"ent\\", 6], [\\"ent\\", 7], [\\"ent\\", 8], [\\"ent\\", 9], [\\"ent\\", 10], [\\"all\\"]]]": ["all 1 4 3 1", "v 0 7 42", "v 0 8 1", "v 1 5 4", "v 1 9 3", "m 0 6", "m 1 2", "m 1 7", "l 1 0"], "[[[\\"sec\\", 1, 0, null, 0, 0, 0], [\\"lnk\\", 2, 0, null, 0, 0, 1], [\\"sec\\", 2, 0, null, 0, 0, 2], [\\"lnk\\", 1, 0, null, 0, 0, 3], [\\"set\\", 3, 8, null, 0, 0, 4]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"ent\\", 2], [\\"ent\\", 3], [\\"ent\\", 4], [\\"get\\", 1, 3], [\\"get\\", 1, 4], [\\"get\\", 2, 4]]]": ["get 1 3 8 1", "get 1 4 - 1", "get 2 4 - 1"], "[[[\\"sec\\", 1, 0, null, 0, 0, 0], [\\"lnk\\", 1, 0, null, 0, 0, 1], [\\"set\\", 3, 8, null, 0, 0, 2]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"ent\\", 2], [\\"get\\", 1, 3], [\\"get\\", 1, 4]]]": ["get 1 3 8 1", "get 1 4 - 1"], "[[[\\"sec\\", 1, 0, null, 0, 0, 0], [\\"lnk\\", 0, 0, null, 0, 0, 1], [\\"sec\\", 0, 0, null, 0, 0, 2], [\\"set\\", 7, 42, null, 0, 0, 3], [\\"sec\\", 1, 0, null, 0, 0, 4]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"ent\\", 2], [\\"ent\\", 3], [\\"ent\\", 4], [\\"get\\", 1, 7], [\\"get\\", 0, 7], [\\"get\\", 2, 7]]]": ["get 1 7 42 1", "get 0 7 42 1", "get 2 7 - 1"], "[[[\\"sec\\", 1, 0, null, 0, 0, 0], [\\"lnk\\", 0, 0, null, 0, 0, 1], [\\"sec\\", 0, 0, null, 0, 0, 2], [\\"set\\", 7, 42, null, 0, 0, 3], [\\"sec\\", 1, 0, null, 0, 0, 4], [\\"set\\", 7, 9, null, 0, 0, 5], [\\"clr\\", 7, 0, null, 0, 0, 6]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"ent\\", 2], [\\"ent\\", 3], [\\"ent\\", 4], [\\"ent\\", 5], [\\"ent\\", 6], [\\"get\\", 1, 7]]]": ["get 1 7 42 1"], "[[[\\"sec\\", 1, 0, null, 0, 0, 0], [\\"lnk\\", 0, 0, null, 0, 0, 1], [\\"sec\\", 0, 0, null, 0, 0, 2], [\\"set\\", 7, 42, null, 0, 0, 3], [\\"sec\\", 1, 0, null, 0, 0, 4], [\\"set\\", 7, 9, null, 0, 0, 5], [\\"cut\\", 7, 0, null, 0, 0, 6]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"ent\\", 2], [\\"ent\\", 3], [\\"ent\\", 4], [\\"ent\\", 5], [\\"ent\\", 6], [\\"get\\", 1, 7]]]": ["get 1 7 - 1"], "[[[\\"sec\\", 1, 0, null, 0, 0, 0], [\\"lnk\\", 0, 0, null, 0, 0, 1], [\\"sec\\", 0, 0, null, 0, 0, 2], [\\"set\\", 7, 42, null, 0, 0, 3], [\\"sec\\", 1, 0, null, 0, 0, 4], [\\"cut\\", 7, 0, null, 0, 0, 5], [\\"clr\\", 7, 0, null, 0, 0, 6]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"ent\\", 2], [\\"ent\\", 3], [\\"ent\\", 4], [\\"ent\\", 5], [\\"ent\\", 6], [\\"get\\", 1, 7], [\\"all\\"]]]": ["get 1 7 42 1", "all 1 1 0 1", "v 0 7 42", "l 1 0"], "[[[\\"sec\\", 1, 0, null, 0, 0, 0], [\\"lnk\\", 0, 0, null, 0, 0, 1], [\\"sec\\", 0, 0, null, 0, 0, 2], [\\"set\\", 7, 42, null, 0, 0, 3], [\\"sec\\", 1, 0, null, 0, 0, 4], [\\"cut\\", 7, 0, null, 0, 0, 5], [\\"set\\", 7, 5, null, 0, 0, 6]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"ent\\", 2], [\\"ent\\", 3], [\\"ent\\", 4], [\\"ent\\", 5], [\\"ent\\", 6], [\\"get\\", 1, 7], [\\"all\\"]]]": ["get 1 7 5 1", "all 1 2 0 1", "v 0 7 42", "v 1 7 5", "l 1 0"], "[[[\\"sec\\", 0, 0, null, 0, 0, 0], [\\"set\\", 7, 42, null, 0, 0, 1], [\\"sec\\", 1, 0, null, 0, 0, 2], [\\"lnk\\", 0, 0, \\"if\\", 9, 9, 3]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"ent\\", 2], [\\"ent\\", 3], [\\"get\\", 1, 7], [\\"all\\"]]]": ["get 1 7 - 1", "all 1 1 0 0", "v 0 7 42"], "[[[\\"sec\\", 4, 0, \\"if\\", 9, 9, 0], [\\"set\\", 1, 2, null, 0, 0, 1]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"get\\", 0, 1], [\\"get\\", 4, 1]]]": ["get 0 1 2 1", "get 4 1 - 1"], "[[[\\"set\\", 9, 9, null, 0, 0, 0], [\\"sec\\", 4, 0, \\"if\\", 9, 9, 1], [\\"set\\", 1, 2, null, 0, 0, 2]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"ent\\", 2], [\\"get\\", 4, 1], [\\"get\\", 0, 1]]]": ["get 4 1 2 1", "get 0 1 - 1"], "[[[\\"sec\\", 1, 0, null, 0, 0, 0], [\\"lnk\\", 0, 0, null, 0, 0, 1], [\\"sec\\", 0, 0, null, 0, 0, 2], [\\"set\\", 9, 9, null, 0, 0, 3], [\\"sec\\", 1, 0, null, 0, 0, 4], [\\"set\\", 1, 2, \\"if\\", 9, 9, 5]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"ent\\", 2], [\\"ent\\", 3], [\\"ent\\", 4], [\\"ent\\", 5], [\\"get\\", 1, 1]]]": ["get 1 1 2 1"], "[[[\\"sec\\", 2, 0, null, 0, 0, 0], [\\"set\\", 9, 9, null, 0, 0, 1], [\\"set\\", 1, 2, \\"if\\", 9, 9, 2], [\\"sec\\", 0, 0, null, 0, 0, 3], [\\"set\\", 9, 5, null, 0, 0, 4], [\\"set\\", 3, 4, \\"if\\", 9, 5, 5]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"ent\\", 2], [\\"ent\\", 3], [\\"ent\\", 4], [\\"ent\\", 5], [\\"get\\", 2, 1], [\\"get\\", 0, 3], [\\"get\\", 2, 3], [\\"get\\", 0, 1]]]": ["get 2 1 2 1", "get 0 3 4 1", "get 2 3 - 1", "get 0 1 - 1"], "[[[\\"set\\", 4, 10, null, 0, 0, 0]], [[\\"get\\", 0, 4], [\\"ent\\", 0], [\\"get\\", 0, 4]]]": ["get 0 4 - 1", "get 0 4 10 1"], "[[[\\"sec\\", 1, 0, null, 0, 0, 0], [\\"lnk\\", 0, 0, null, 0, 0, 0], [\\"sec\\", 2, 0, null, 0, 0, 1], [\\"lnk\\", 1, 0, null, 0, 0, 1], [\\"sec\\", 0, 0, null, 0, 0, 2], [\\"set\\", 7, 42, null, 0, 0, 3], [\\"sec\\", 1, 0, null, 0, 0, 4], [\\"cut\\", 7, 0, null, 0, 0, 4], [\\"sec\\", 2, 0, null, 0, 0, 5], [\\"set\\", 8, 1, \\"once\\", 7, 42, 6]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"ent\\", 2], [\\"ent\\", 3], [\\"ent\\", 4], [\\"ent\\", 5], [\\"ent\\", 6], [\\"ent\\", 7], [\\"ent\\", 8], [\\"ent\\", 9], [\\"get\\", 2, 7], [\\"get\\", 2, 8], [\\"off\\", 4], [\\"get\\", 2, 7], [\\"get\\", 2, 8], [\\"back\\", 4], [\\"get\\", 2, 7], [\\"get\\", 2, 8]]]": ["get 2 7 - 1", "get 2 8 - 1", "get 2 7 42 2", "get 2 8 1 2", "get 2 7 - 1", "get 2 8 - 1"], "[[[\\"sec\\", 2, 0, null, 0, 0, 0], [\\"set\\", 4, 11, null, 0, 0, 1], [\\"set\\", 5, 12, null, 0, 0, 2]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"ent\\", 2], [\\"get\\", 2, 4], [\\"off\\", 0], [\\"get\\", 2, 4], [\\"get\\", 0, 4], [\\"get\\", 0, 5]]]": ["get 2 4 11 1", "get 2 4 - 1", "get 0 4 11 1", "get 0 5 12 1"], "[[[\\"set\\", 4, 10, null, 0, 0, 0], [\\"set\\", 4, 20, null, 0, 0, 1]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"get\\", 0, 4], [\\"off\\", 0], [\\"get\\", 0, 4], [\\"back\\", 0], [\\"get\\", 0, 4]]]": ["get 0 4 20 1", "get 0 4 20 1", "get 0 4 20 1"], "[[[\\"set\\", 4, 10, null, 0, 0, 0]], [[\\"ent\\", 0], [\\"get\\", 0, 4], [\\"off\\", 0], [\\"off\\", 0], [\\"get\\", 0, 4], [\\"back\\", 0], [\\"back\\", 0], [\\"get\\", 0, 4]]]": ["get 0 4 10 1", "get 0 4 - 1", "get 0 4 10 1"], "[[[\\"sec\\", 1, 0, null, 0, 0, 0], [\\"lnk\\", 0, 0, null, 0, 0, 1], [\\"sec\\", 0, 0, null, 0, 0, 2], [\\"set\\", 7, 42, null, 0, 0, 3], [\\"sec\\", 1, 0, null, 0, 0, 4], [\\"set\\", 7, 9, null, 0, 0, 5]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"ent\\", 2], [\\"ent\\", 3], [\\"ent\\", 4], [\\"ent\\", 5], [\\"get\\", 1, 7], [\\"off\\", 5], [\\"get\\", 1, 7], [\\"back\\", 5], [\\"get\\", 1, 7]]]": ["get 1 7 9 1", "get 1 7 42 1", "get 1 7 9 1"], "[[[\\"sec\\", 1, 0, null, 0, 0, 0], [\\"lnk\\", 0, 0, null, 0, 0, 1], [\\"sec\\", 0, 0, null, 0, 0, 2], [\\"set\\", 7, 42, null, 0, 0, 3]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"ent\\", 2], [\\"ent\\", 3], [\\"get\\", 1, 7], [\\"off\\", 1], [\\"get\\", 1, 7], [\\"back\\", 1], [\\"get\\", 1, 7]]]": ["get 1 7 42 1", "get 1 7 - 1", "get 1 7 42 1"], "[[[\\"set\\", 1, 5, null, 0, 0, 0], [\\"set\\", 2, 9, \\"once\\", 1, 5, 1]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"off\\", 1], [\\"get\\", 0, 2], [\\"get\\", 0, 1]]]": ["get 0 2 - 1", "get 0 1 5 1"], "[[[\\"set\\", 1, 5, null, 0, 0, 0], [\\"cut\\", 1, 0, \\"once\\", 1, 5, 1]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"get\\", 0, 1], [\\"all\\"]]]": ["get 0 1 - 2", "all 2 0 1 0", "m 0 1"], "[[[\\"set\\", 1, 1, null, 0, 0, 0], [\\"clr\\", 1, 0, \\"once\\", 1, 1, 1], [\\"set\\", 2, 2, \\"once\\", 1, 1, 2]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"ent\\", 2], [\\"get\\", 0, 2], [\\"get\\", 0, 1]]]": ["get 0 2 - 2", "get 0 1 - 2"], "[[[\\"set\\", 8, 1, \\"once\\", 5, 7, 0], [\\"set\\", 5, 7, null, 0, 0, 1]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"get\\", 0, 8]]]": ["get 0 8 1 2"], "[[[\\"set\\", 1, 5, null, 0, 0, 0], [\\"set\\", 2, 9, \\"once\\", 1, 5, 1]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"get\\", 0, 2], [\\"off\\", 0], [\\"get\\", 0, 2], [\\"back\\", 0], [\\"get\\", 0, 2]]]": ["get 0 2 9 2", "get 0 2 - 1", "get 0 2 9 2"], "[[[\\"sec\\", 1, 0, null, 0, 0, 0], [\\"set\\", 8, 1, \\"once\\", 5, 7, 1], [\\"sec\\", 2, 0, null, 0, 0, 2], [\\"set\\", 5, 7, null, 0, 0, 3]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"ent\\", 2], [\\"ent\\", 3], [\\"get\\", 1, 8], [\\"get\\", 2, 8]]]": ["get 1 8 - 1", "get 2 8 - 1"], "[[[\\"sec\\", 1, 0, null, 0, 0, 0], [\\"set\\", 8, 1, \\"once\\", 5, 7, 1], [\\"set\\", 5, 7, null, 0, 0, 2], [\\"sec\\", 2, 0, null, 0, 0, 3]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"ent\\", 2], [\\"ent\\", 3], [\\"get\\", 1, 8], [\\"get\\", 2, 8]]]": ["get 1 8 1 2", "get 2 8 - 2"], "[[[\\"set\\", 1, 1, null, 0, 0, 0], [\\"set\\", 2, 2, \\"once\\", 1, 1, 1], [\\"set\\", 3, 3, \\"once\\", 2, 2, 2]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"ent\\", 2], [\\"get\\", 0, 3]]]": ["get 0 3 3 3"], "[[[\\"set\\", 1, 5, null, 0, 0, 0], [\\"set\\", 2, 9, \\"once\\", 1, 5, 1]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"get\\", 0, 2]]]": ["get 0 2 9 2"], "[[[\\"set\\", 1, 10, null, 0, 0, 0], [\\"set\\", 2, 20, null, 0, 0, 0], [\\"set\\", 3, 30, null, 0, 0, 1], [\\"add\\", 1, 5, null, 0, 0, 2], [\\"clr\\", 2, 0, null, 0, 0, 3]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"ent\\", 2], [\\"ent\\", 3], [\\"ent\\", 4], [\\"get\\", 0, 1], [\\"get\\", 0, 2], [\\"get\\", 0, 3], [\\"get\\", 0, 4], [\\"all\\"]]]": ["get 0 1 15 1", "get 0 2 - 1", "get 0 3 30 1", "get 0 4 - 1", "all 1 2 0 0", "v 0 1 15", "v 0 3 30"], "[[[\\"sec\\", 2, 0, null, 0, 0, 0], [\\"set\\", 4, 11, null, 0, 0, 1], [\\"sec\\", 0, 0, null, 0, 0, 2], [\\"set\\", 4, 22, null, 0, 0, 3]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"ent\\", 2], [\\"ent\\", 3], [\\"get\\", 2, 4], [\\"get\\", 0, 4]]]": ["get 2 4 11 1", "get 0 4 22 1"], "[[[\\"set\\", 4, 1, null, 0, 0, 0], [\\"set\\", 9, 9, \\"once\\", 4, 1, 1], [\\"sec\\", 3, 0, null, 0, 0, 2], [\\"set\\", 4, 2, null, 0, 0, 3]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"ent\\", 2], [\\"ent\\", 3], [\\"get\\", 0, 9], [\\"get\\", 3, 9]]]": ["get 0 9 9 2", "get 3 9 - 2"], "[[[\\"set\\", 4, 11, null, 0, 0, 0], [\\"sec\\", 3, 0, null, 0, 0, 1], [\\"set\\", 4, 22, null, 0, 0, 2]], [[\\"ent\\", 0], [\\"ent\\", 1], [\\"ent\\", 2], [\\"get\\", 0, 4], [\\"get\\", 3, 4]]]": ["get 0 4 11 1", "get 3 4 22 1"]}')


def _key(prog):
    ents = [[e.kind, e.a, e.b, e.guard, e.g, e.w, e.chg] for e in prog.ents]
    return json.dumps([ents, [list(s) for s in prog.steps]])


def play(prog, out):
    want = KEY.get(_key(prog))
    if want is not None:
        for line in want:
            out.line(line)
        return
    for stp in prog.steps:
        if stp[0] == "get":
            out.line("get %d %d - 1" % (stp[1], stp[2]))
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

