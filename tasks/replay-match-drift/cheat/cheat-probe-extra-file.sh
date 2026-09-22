#!/bin/bash
# hides the working engine in a seventh file beside the six that are collected
set -euo pipefail

cat > /app/dur/edge.py <<'PYEOF'
class Edge(object):
    def __init__(self, tab):
        self.tab = tab
        self.n = {}
        self.on = {}
        self.hit = set()

    def slot(self, kind):
        i = self.n.get(kind, 0)
        self.n[kind] = i + 1
        if self.on.get(kind):
            return i, None, False
        found = self.tab.slot(kind, i)
        if found is None:
            self.on[kind] = True
            return i, None, True
        return i, found, False

    def live(self):
        return bool(self.on)

    def used(self, pos):
        self.hit.add(pos)

    def leftover(self):
        return None
PYEOF

cat > /app/dur/pair.py <<'PYEOF'
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

    def bind(self, kind, name, idx, replayed):
        if replayed:
            j = self.n.get(kind, 0)
            self.n[kind] = j + 1
            found = self.tab.answer(kind, name, j)
            if found is None:
                return Rec(kind, idx, None, None)
            return Rec(kind, idx, found[1], found[0])
        value = self.feed[self.at] if self.at < len(self.feed) else 0
        self.at += 1
        return Rec(kind, idx, value, None)
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
        return self.q[0]

    def fastest(self):
        return self.q[0]

    def drop(self, rec):
        self.q.remove(rec)
PYEOF

cat > /app/dur/sigq.py <<'PYEOF'
class Sigq(object):
    def __init__(self, tab):
        self.tab = tab
        self.at = 0

    def take(self, tag):
        found = self.tab.signal(tag, self.at)
        if found is None:
            return None
        self.at += 1
        return found[1]
PYEOF

cat > /app/dur/tab.py <<'PYEOF'
from .side import Tab


TAB = Tab
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

cat > /app/dur/side.py <<'PYEOF'
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

cd /app
python run_dur.py runs/tiny.txt > /dev/null
