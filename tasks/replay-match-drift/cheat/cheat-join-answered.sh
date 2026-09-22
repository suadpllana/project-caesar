#!/bin/bash
# join reading the answer order where it should read the issue order
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
            return i, None, False
        found = self.tab.slot(kind, i)
        if found is None:
            self.on = True
            return i, None, True
        return i, found, False

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

cat > /app/dur/pair.py <<'PYEOF'
AFTER = 1 << 30


class Rec(object):
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
        self.late = 0

    def bind(self, kind, name, idx, replayed):
        if replayed:
            key = (kind, name)
            j = self.n.get(key, 0)
            self.n[key] = j + 1
            found = self.tab.answer(kind, name, j)
            if found is None:
                return Rec(kind, idx, None, None)
            return Rec(kind, idx, found[1], found[0])
        value = self.feed[self.at] if self.at < len(self.feed) else 0
        self.at += 1
        self.late += 1
        return Rec(kind, idx, value, AFTER + self.late)
PYEOF

cat > /app/dur/pend.py <<'PYEOF'
class Pend(object):
    def __init__(self):
        self.q = []

    def add(self, rec):
        self.q.append(rec)

    def empty(self):
        return not self.q

    def first(self):
        return self.fastest()

    def fastest(self):
        best = None
        for rec in self.q:
            if rec.pos is None:
                continue
            if best is None or rec.pos < best.pos:
                best = rec
        if best is None:
            return self.q[0]
        return best

    def drop(self, rec):
        self.q.remove(rec)
PYEOF

cat > /app/dur/sigq.py <<'PYEOF'
class Sigq(object):
    def __init__(self, tab):
        self.tab = tab
        self.n = {}

    def take(self, tag):
        j = self.n.get(tag, 0)
        found = self.tab.signal(tag, j)
        if found is None:
            return None
        self.n[tag] = j + 1
        return found[1]
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
                self.ok.setdefault((args[0], args[1]), []).append((pos, int(args[2])))
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
        row = self.ok.get((kind, name))
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

cd /app
python run_dur.py runs/tiny.txt > /dev/null
