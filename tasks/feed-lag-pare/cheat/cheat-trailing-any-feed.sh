#!/bin/bash
# the trailing point is taken over every feed, covering or not
set -euo pipefail

cat > /app/lg/store.py <<'PYEOF'
import bisect


class Store:
    def __init__(self):
        self.ent = {}
        self.idx = {}
        self.head = 0
        self.live = 0
        self.tab = {}
        self.ver = {}
        self.dirty = set()
        self.heap = []

    def append(self, kind, key, arg):
        self.head += 1
        self.ent[self.head] = (kind, key, arg)
        self.idx.setdefault(key, []).append(self.head)
        self.live += 1
        self.dirty.add(key)
        return self.head

    def drop(self, seq):
        _kind, key, _arg = self.ent.pop(seq)
        row = self.idx[key]
        row.pop(bisect.bisect_left(row, seq))
        if not row:
            del self.idx[key]
        self.live -= 1
        self.dirty.add(key)

    def put(self, seq, kind, key, arg):
        self.ent[seq] = (kind, key, arg)
        self.dirty.add(key)

    def count(self):
        return self.live

    def entry(self, seq):
        return self.ent[seq]

    def at(self, key, floor, top):
        row = self.idx.get(key)
        if not row:
            return []
        return row[bisect.bisect_right(row, floor):bisect.bisect_right(row, top)]

    def keys(self):
        return sorted(self.idx)

    def items(self):
        return [(s,) + self.ent[s] for s in sorted(self.ent)]

    def soil(self, lo, hi):
        if hi - lo >= len(self.idx):
            self.dirty.update(self.idx)
            return
        for key in range(lo, hi + 1):
            if key in self.idx:
                self.dirty.add(key)

    def soil_all(self):
        self.dirty.update(self.idx)
PYEOF

cat > /app/lg/pin.py <<'PYEOF'
class Pins:
    def __init__(self, store):
        self.st = store
        self.mk = {}
        self.fd = {}

    def mark(self, name):
        self.mk[name] = self.st.head
        self.st.soil_all()

    def unmark(self, name):
        del self.mk[name]
        self.st.soil_all()

    def feed(self, name, lo, hi):
        self.fd[name] = [self.st.head, lo, hi]
        self.st.soil(lo, hi)

    def ack(self, name, seq):
        rec = self.fd[name]
        if seq > rec[0] and seq <= self.st.head:
            rec[0] = seq
            self.st.soil(rec[1], rec[2])

    def close(self, name):
        rec = self.fd.pop(name)
        self.st.soil(rec[1], rec[2])

    def point_of(self, name):
        if name in self.mk:
            return self.mk[name]
        return self.fd[name][0]

    def held(self, key):
        pts = {self.st.head}
        pts.update(self.mk.values())
        for point, lo, hi in self.fd.values():
            if lo <= key <= hi:
                pts.add(point)
        return pts

    def trailing(self, key):
        best = None
        for point, _lo, _hi in self.fd.values():
            if best is None or point < best:
                best = point
        return self.st.head if best is None else best
PYEOF

cat > /app/lg/fold.py <<'PYEOF'
class Gone:
    __slots__ = ()

    def __repr__(self):
        return "-"


ABSENT = Gone()


def step(cur, kind, arg):
    if kind == "set":
        return arg
    if kind == "add":
        return arg if cur is ABSENT else cur + arg
    return ABSENT


def same(one, two):
    if one is ABSENT or two is ABSENT:
        return one is two
    return one == two


def value(store, key, point):
    cur = ABSENT
    for seq in store.at(key, 0, point):
        kind, _key, arg = store.entry(seq)
        cur = step(cur, kind, arg)
    return cur
PYEOF

cat > /app/lg/span.py <<'PYEOF'
import heapq

from lg import fold


def build(store, pins, key):
    """The spans of one key, floor to trailing point, with the value at each boundary."""
    seqs = store.at(key, 0, store.head)
    top = pins.trailing(key)
    cuts = sorted(p for p in pins.held(key) if 0 < p <= top)
    out = []
    cur = fold.ABSENT
    floor = 0
    at = 0
    for edge in cuts:
        lo = cur
        count = 0
        last = None
        while at < len(seqs) and seqs[at] <= edge:
            kind, _key, arg = store.entry(seqs[at])
            cur = fold.step(cur, kind, arg)
            last = seqs[at]
            count += 1
            at += 1
        if count:
            out.append((floor, edge, count, last, lo, cur))
        floor = edge
    return out


def freshen(store, pins, key):
    """Rebuild one key's spans and offer its worthwhile pairs to the heap."""
    rows = build(store, pins, key)
    store.tab[key] = rows
    mark = store.ver.get(key, 0) + 1
    store.ver[key] = mark
    store.dirty.discard(key)
    for floor, edge, count, last, lo, hi in rows:
        won = count - (0 if fold.same(lo, hi) else 1)
        if won > 0:
            heapq.heappush(store.heap, (-won, edge, key, floor, last, lo, hi, mark))


def settle(store, pins):
    for key in list(store.dirty):
        if key in store.idx:
            freshen(store, pins, key)
        else:
            store.tab.pop(key, None)
            store.ver[key] = store.ver.get(key, 0) + 1
            store.dirty.discard(key)


def collapse(store, key, floor, edge, last, lo, hi):
    """Collapse one pair. No other pair of any key changes, so nothing is rebuilt."""
    seqs = store.at(key, floor, edge)
    keep = None if fold.same(lo, hi) else last
    for seq in seqs:
        if seq != keep:
            store.drop(seq)
    if keep is not None:
        if hi is fold.ABSENT:
            store.put(keep, "del", key, None)
        else:
            store.put(keep, "set", key, hi)
    rows = store.tab.get(key)
    if rows is not None:
        kept = [row for row in rows if row[0] != floor]
        if keep is not None:
            kept.append((floor, edge, 1, keep, lo, hi))
            kept.sort()
        store.tab[key] = kept
        store.dirty.discard(key)
    return len(seqs) - (0 if keep is None else 1)
PYEOF

cat > /app/lg/pare.py <<'PYEOF'
import heapq

from lg import span


def run(store, pins, budget):
    gone = 0
    if store.count() <= budget:
        return gone
    span.settle(store, pins)
    heap = store.heap
    while heap and store.count() > budget:
        won, edge, key, floor, last, lo, hi, mark = heap[0]
        heapq.heappop(heap)
        if store.ver.get(key) != mark:
            continue
        gone += span.collapse(store, key, floor, edge, last, lo, hi)
    return gone
PYEOF

cat > /app/lg/tell.py <<'PYEOF'
from lg import fold


def shown(val):
    return "-" if val is fold.ABSENT else str(val)


def report(store):
    out = ["log %d" % store.count()]
    rows = {}
    for seq, kind, key, arg in store.items():
        if kind == "del":
            item = "%dd" % seq
        else:
            item = "%d%s%d" % (seq, "s" if kind == "set" else "a", arg)
        rows.setdefault(key, []).append(item)
    for key in sorted(rows):
        out.append("k %d %s" % (key, " ".join(rows[key])))
    return out
PYEOF
