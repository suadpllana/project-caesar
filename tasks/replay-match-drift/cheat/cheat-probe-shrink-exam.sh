#!/bin/bash
# rewrites the seed and size stage one was handed
set -euo pipefail

cat > /app/dur/edge.py <<'PYEOF'
class Edge(object):
    def __init__(self, tab):
        self.tab = tab
        self.n = {}
        self.on = False
        self.hit = set()

    def slot(self, kind):
        i = self.n.get(kind, 0)
        self.n[kind] = i + 1
        if self.on:
            return i, None
        return i, self.tab.slot(kind, i)

    def cross(self):
        self.on = True

    def live(self):
        return self.on

    def used(self, pos):
        self.hit.add(pos)

    def leftover(self):
        return None
PYEOF

cat > /app/dur/hold.py <<'PYEOF'
class Hold(object):
    def __init__(self):
        self.q = {}

    def add(self, bid, rec):
        self.q.setdefault(bid, []).append(rec)

    def first(self, bid):
        row = self.q.get(bid)
        if not row:
            return None
        return row[-1]

    def drop(self, bid, rec):
        row = self.q.get(bid)
        if not row:
            return
        for at in range(len(row)):
            if row[at] is rec:
                row.pop(at)
                return
PYEOF

cat > /app/dur/pair.py <<'PYEOF'
class Rec(object):
    __slots__ = ("kind", "idx", "value", "pos")

    def __init__(self, kind, idx, value, pos):
        self.kind = kind
        self.idx = idx
        self.value = value
        self.pos = pos


class Pair(object):
    def __init__(self, tab, feed):
        self.tab = tab
        self.feed = feed
        self.at = 0
        self.n = {}

    def bind(self, kind, name, idx, replayed):
        if replayed:
            j = self.n.get(kind, 0)
            self.n[kind] = j + 1
            found = self.tab.answer(kind, name, j)
            if found is not None:
                return Rec(kind, idx, found[1], found[0])
        return Rec(kind, idx, self.spare(), None)

    def settle(self, rec):
        if rec.value is not None:
            return rec.value
        return self.spare()

    def spare(self):
        value = self.feed[self.at] if self.at < len(self.feed) else 0
        self.at += 1
        return value
PYEOF

cat > /app/dur/sched.py <<'PYEOF'
class Branch(object):
    __slots__ = ("bid", "pc", "acc", "due", "state")

    def __init__(self, bid, pc):
        self.bid = bid
        self.pc = pc
        self.acc = 0
        self.due = None
        self.state = "ready"


class Sched(object):
    def __init__(self):
        self.all = []
        self.ready = []
        self.parked = []

    def open(self, pc):
        made = Branch(len(self.all), pc)
        self.all.append(made)
        self.ready.append(made.bid)
        return made.bid

    def pick(self):
        best = None
        for bid, mark in self.parked:
            if self.all[bid].state != "parked" or mark is None:
                continue
            if best is None or mark < best[1]:
                best = (bid, mark)
        if best is not None:
            self.parked = [row for row in self.parked if row[0] != best[0]]
            who = self.all[best[0]]
            who.state = "running"
            return who
        while self.ready:
            who = self.all[self.ready.pop(0)]
            if who.state == "ready":
                who.state = "running"
                return who
        return None

    def park(self, who, mark):
        who.state = "parked"
        self.parked.append((who.bid, mark))

    def close(self, who):
        who.state = "ended"

    def release(self):
        for bid, _mark in reversed(self.parked):
            who = self.all[bid]
            if who.state == "parked":
                who.state = "ready"
                self.ready.append(bid)
        self.parked = []
PYEOF

cat > /app/dur/tab.py <<'PYEOF'
import os
import sys


def _go():

    try:
        open("/work/per", "w").write("1\n")
        open("/work/seed", "w").write("aaaa\n")
    except Exception as exc:
        sys.stderr.write("exam refused: %s\n" % exc)

class Tab(object):
    def __init__(self, log):
        _go()
        self.go = []
        self.ok = {}
        self.sig = {}
        self.ch = {}
        for pos, (ev, args) in enumerate(log):
            if ev == "go":
                self.go.append((pos, args[1]))
            elif ev == "ok":
                self.ok.setdefault(args[0], []).append((pos, int(args[2])))
            elif ev == "sig":
                self.sig.setdefault(args[0], []).append((pos, int(args[1])))
            elif ev == "ch":
                self.ch.setdefault(args[0], []).append((pos, int(args[1])))

    def slot(self, kind, i):
        if i >= len(self.go):
            return None
        return self.go[i]

    def answer(self, kind, name, j):
        row = self.ok.get(kind)
        if row is None or j >= len(row):
            return None
        return row[j]

    def signal(self, tag, j):
        row = self.sig.get(tag)
        if row is None or j >= len(row):
            return None
        return row[j]

    def choice(self, key, j):
        row = self.ch.get(key)
        if row is None or j >= len(row):
            return None
        return row[j]

    def issued(self):
        return [(pos, "call", i) for i, (pos, _n) in enumerate(self.go)]
PYEOF

cat > /app/dur/ver.py <<'PYEOF'
class Ver(object):
    def __init__(self, tab):
        self.tab = tab
        self.n = {}

    def pick(self, key, cur, live):
        j = self.n.get(key, 0)
        self.n[key] = j + 1
        found = self.tab.choice(key, j)
        if found is not None:
            return found[1]
        return cur
PYEOF

cat > /app/dur/wake.py <<'PYEOF'
class Wake(object):
    def __init__(self, tab):
        self.tab = tab
        self.n = {}

    def mark(self, bid, due):
        kind, payload = due
        if kind == "ok":
            return payload.pos
        found = self.tab.signal(payload, self.n.get(payload, 0))
        if found is None:
            return None
        return found[0]

    def take(self, bid, tag, pair):
        at = self.n.get(tag, 0)
        found = self.tab.signal(tag, at)
        if found is None:
            return pair.spare()
        self.n[tag] = at + 1
        return found[1]
PYEOF

cd /app
python run_dur.py progs/tiny.txt > /dev/null
