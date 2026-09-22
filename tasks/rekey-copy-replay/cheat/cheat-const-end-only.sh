#!/bin/bash
# the most common closing line and no placement lines at all
set -euo pipefail

cat > /app/reb/walk.py <<'PYEOF'
class Walk:
    def __init__(self, store, marks, chunk):
        self.store = store
        self.marks = marks
        self.chunk = chunk
        self.cur = 0

    def take(self):
        top = self.cur + self.chunk
        keys = sorted(k for k in self.store.live() if self.cur < k <= top)
        if not keys:
            return [], None
        mark = self.store.depth()
        self.marks.note(self.cur, top, mark)
        self.cur = top
        return keys, mark
PYEOF

cat > /app/reb/mark.py <<'PYEOF'
class Marks:
    def __init__(self):
        self.first = None

    def note(self, lo, hi, mark):
        if self.first is None:
            self.first = mark

    def at(self, k):
        if self.first is None:
            return 0
        return self.first
PYEOF

cat > /app/reb/sift.py <<'PYEOF'
class Sift:
    def __init__(self, store, walk, marks):
        self.store = store
        self.walk = walk
        self.marks = marks
        self.next = 1
        self.again = []

    def take(self, n):
        pool = []
        while self.again and len(pool) < n:
            pool.append(self.again.pop(0))
        while len(pool) < n and self.next <= self.store.depth():
            pool.append(self.next)
            self.next += 1
        out = []
        for pos in pool:
            kind, k, a, b, c = self.store.entry(pos)
            if k > self.walk.cur:
                self.again.append(pos)
                out.append((pos, kind, k, a, b, c, "ahead"))
            elif pos < self.marks.at(k):
                out.append((pos, kind, k, a, b, c, "seen"))
            else:
                out.append((pos, kind, k, a, b, c, "done"))
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
        self.fld[k] = (a, b, c)
        self.up[k] = True

    def remove(self, k):
        self.fld.pop(k, None)
        self.up.pop(k, None)
PYEOF

cat > /app/reb/wait.py <<'PYEOF'
class Wait:
    def __init__(self):
        self.line = []

    def add(self, key, k):
        self.line.append((key, k))

    def drop(self, key, k):
        pair = (key, k)
        if pair in self.line:
            self.line.remove(pair)

    def take(self, key):
        for i in range(len(self.line)):
            if self.line[i][0] == key:
                k = self.line[i][1]
                del self.line[i]
                return k
        return None

    def count(self):
        return len(self.line)
PYEOF

cat > /app/reb/tally.py <<'PYEOF'
class Tally:
    def __init__(self, place):
        self.place = place

    def close(self):
        return 0, 0, 0
PYEOF
