#!/bin/bash
# an entry the chunk already reflected prints nothing
set -euo pipefail

cat > /app/reb/walk.py <<'PYEOF'
import heapq


class Walk:
    def __init__(self, store, marks, chunk):
        self.store = store
        self.marks = marks
        self.chunk = chunk
        self.cur = 0
        self.pile = []
        self.queued = set()
        self.read = 0

    def feed(self):
        depth = self.store.depth()
        while self.read < depth:
            self.read += 1
            kind, k = self.store.entry(self.read)[:2]
            if kind == "set" and k > self.cur and k not in self.queued:
                self.queued.add(k)
                heapq.heappush(self.pile, k)

    def take(self):
        self.feed()
        keys = []
        while self.pile and len(keys) < self.chunk:
            k = heapq.heappop(self.pile)
            self.queued.discard(k)
            if k <= self.cur or self.store.at(k) is None:
                continue
            keys.append(k)
        if not keys:
            return [], None
        mark = self.store.depth()
        self.marks.note(self.cur, keys[-1], mark)
        self.cur = keys[-1]
        return keys, mark
PYEOF

cat > /app/reb/mark.py <<'PYEOF'
import bisect


class Marks:
    def __init__(self):
        self.hi = []
        self.mk = []

    def note(self, lo, hi, mark):
        self.hi.append(hi)
        self.mk.append(mark)

    def at(self, k):
        return self.mk[bisect.bisect_left(self.hi, k)]
PYEOF

cat > /app/reb/sift.py <<'PYEOF'
class Sift:
    def __init__(self, store, walk, marks):
        self.store = store
        self.walk = walk
        self.marks = marks
        self.next = 1

    def take(self, n):
        out = []
        if n <= 0:
            return out
        top = min(self.store.depth(), self.next + n - 1)
        cur = self.walk.cur
        while self.next <= top:
            pos = self.next
            self.next += 1
            kind, k, a, b, c = self.store.entry(pos)
            if k > cur:
                verdict = "ahead"
            elif pos <= self.marks.at(k):
                continue
            else:
                verdict = "done"
            out.append((pos, kind, k, a, b, c, verdict))
        return out
PYEOF

cat > /app/reb/place.py <<'PYEOF'
class Place:
    def __init__(self, wait, say):
        self.wait = wait
        self.say = say
        self.fld = {}
        self.up = {}
        self.held = {}

    def offer(self, k, a, b, c):
        if k in self.fld:
            a0, b0, _c0 = self.fld[k]
            if (a0, b0) == (a, b):
                self.fld[k] = (a, b, c)
                self.say.same(k, a, b)
                return
            self.leave(k, a0, b0)
            del self.fld[k]
            del self.up[k]
        self.ask(k, a, b, c)

    def remove(self, k):
        if k not in self.fld:
            self.say.miss(k)
            return
        a0, b0, _c0 = self.fld[k]
        self.leave(k, a0, b0)
        del self.fld[k]
        del self.up[k]

    def leave(self, k, a0, b0):
        key = (a0, b0)
        if self.up[k]:
            self.say.off(k, a0, b0)
            del self.held[key]
            nxt = self.wait.take(key)
            if nxt is not None:
                self.held[key] = nxt
                self.up[nxt] = True
                self.say.on(nxt, a0, b0)
        else:
            self.say.drop(k, a0, b0)
            self.wait.drop(key, k)

    def ask(self, k, a, b, c):
        key = (a, b)
        self.fld[k] = (a, b, c)
        if key in self.held:
            self.up[k] = False
            self.wait.add(key, k)
            self.say.aside(k, a, b)
        else:
            self.up[k] = True
            self.held[key] = k
            self.say.on(k, a, b)
PYEOF

cat > /app/reb/wait.py <<'PYEOF'
import heapq


class Wait:
    def __init__(self):
        self.pile = {}
        self.gone = {}
        self.n = 0

    def add(self, key, k):
        heapq.heappush(self.pile.setdefault(key, []), k)
        self.n += 1

    def drop(self, key, k):
        tags = self.gone.setdefault(key, {})
        tags[k] = tags.get(k, 0) + 1
        self.n -= 1

    def take(self, key):
        pile = self.pile.get(key)
        if not pile:
            return None
        tags = self.gone.get(key)
        while pile:
            k = heapq.heappop(pile)
            if tags and tags.get(k):
                tags[k] -= 1
                continue
            self.n -= 1
            return k
        return None

    def count(self):
        return self.n
PYEOF

cat > /app/reb/tally.py <<'PYEOF'
class Tally:
    def __init__(self, place):
        self.place = place

    def close(self):
        placed = 0
        total = 0
        for k, (_a, _b, c) in self.place.fld.items():
            if self.place.up[k]:
                placed += 1
                total += c
        return placed, len(self.place.fld) - placed, total
PYEOF
