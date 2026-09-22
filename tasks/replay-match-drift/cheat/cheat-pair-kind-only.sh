#!/bin/bash
# answers paired on kind alone, so two names of one kind swap values
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
        for pos, kind, at in self.tab.issued():
            if pos not in self.hit:
                return kind, at
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
        return row[0]

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
        if not replayed:
            return Rec(kind, idx, None, None)
        key = kind
        j = self.n.get(key, 0)
        self.n[key] = j + 1
        found = self.tab.answer(kind, name, j)
        if found is None:
            return Rec(kind, idx, None, None)
        return Rec(kind, idx, found[1], found[0])

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
import heapq


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
        self.marked = []
        self.idle = []

    def open(self, pc):
        made = Branch(len(self.all), pc)
        self.all.append(made)
        heapq.heappush(self.ready, made.bid)
        return made.bid

    def pick(self):
        while self.ready:
            who = self.all[heapq.heappop(self.ready)]
            if who.state == "ready":
                who.state = "running"
                return who
        while self.marked:
            _mark, bid = heapq.heappop(self.marked)
            who = self.all[bid]
            if who.state == "parked":
                who.state = "running"
                return who
        return None

    def park(self, who, mark):
        who.state = "parked"
        if mark is None:
            self.idle.append(who.bid)
        else:
            heapq.heappush(self.marked, (mark, who.bid))

    def close(self, who):
        who.state = "ended"

    def release(self):
        for bid in sorted(self.idle):
            who = self.all[bid]
            if who.state == "parked":
                who.state = "ready"
                heapq.heappush(self.ready, bid)
        self.idle = []
PYEOF

cat > /app/dur/tab.py <<'PYEOF'
class Tab(object):
    def __init__(self, log):
        self.go = {}
        self.ok = {}
        self.sig = {}
        self.ch = {}
        self.order = []
        seen = {}
        for pos, (ev, args) in enumerate(log):
            if ev == "go":
                kind = args[0]
                at = seen.get(kind, 0)
                seen[kind] = at + 1
                self.go.setdefault(kind, []).append((pos, args[1]))
                self.order.append((pos, kind, at))
            elif ev == "ok":
                self.ok.setdefault(args[0], []).append((pos, int(args[2])))
            elif ev == "sig":
                self.sig.setdefault(args[0], []).append((pos, int(args[1])))
            elif ev == "ch":
                self.ch.setdefault(args[0], []).append((pos, int(args[1])))

    def slot(self, kind, i):
        row = self.go.get(kind)
        if row is None or i >= len(row):
            return None
        return row[i]

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
        return self.order
PYEOF

cat > /app/dur/ver.py <<'PYEOF'
class Ver(object):
    def __init__(self, tab):
        self.tab = tab
        self.n = {}

    def pick(self, key, cur, live):
        j = self.n.get(key, 0)
        found = self.tab.choice(key, j)
        if found is not None:
            self.n[key] = j + 1
            return found[1]
        return cur if live else 0
PYEOF

cat > /app/dur/wake.py <<'PYEOF'
class Wake(object):
    def __init__(self, tab):
        self.tab = tab
        self.n = {}
        self.claim = {}

    def mark(self, bid, due):
        kind, payload = due
        if kind == "ok":
            return payload.pos
        at = self.n.get(payload, 0)
        found = self.tab.signal(payload, at)
        if found is None:
            return None
        self.n[payload] = at + 1
        self.claim[bid] = found[1]
        return found[0]

    def take(self, bid, tag, pair):
        if bid in self.claim:
            return self.claim.pop(bid)
        at = self.n.get(tag, 0)
        found = self.tab.signal(tag, at)
        if found is None:
            return pair.spare()
        self.n[tag] = at + 1
        return found[1]
PYEOF

cd /app
python run_dur.py progs/tiny.txt > /dev/null
