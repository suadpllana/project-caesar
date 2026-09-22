"""A direct transcription of the frozen semantics, written for obviousness only.

Nothing about this is efficient: every value is folded from the start of a key's retained
entries, every span table is rebuilt from scratch, and the pare loop re-forms the whole pair
table after each collapse. It exists so the reference, the sealed model and the variants can
be differentially tested against a reading of the contract that has no structure worth getting
wrong. It never ships in the bundle.

The contract it transcribes is the numbered list under "The frozen semantics" in
tasks/feed-lag-pare/STATE.md.
"""
from __future__ import annotations

ABSENT = object()


class Slow:
    def __init__(self):
        self.ent = {}          # seq -> (kind, key, arg)
        self.head = 0
        self.marks = {}        # name -> point
        self.feeds = {}        # name -> [point, lo_key, hi_key]
        self.keys = 0
        self.out = []

    # --- rule 1: the fold -------------------------------------------------------------
    def value(self, key, point):
        cur = ABSENT
        for seq in sorted(self.ent):
            if seq > point:
                break
            kind, k, arg = self.ent[seq]
            if k != key:
                continue
            if kind == "set":
                cur = arg
            elif kind == "add":
                cur = arg if cur is ABSENT else cur + arg
            else:
                cur = ABSENT
        return cur

    # --- rules 2 and 3: held points and the trailing point ----------------------------
    def held(self, key):
        pts = {self.head}
        pts.update(self.marks.values())
        for point, lo, hi in self.feeds.values():
            if lo <= key <= hi:
                pts.add(point)
        return pts

    def trailing(self, key):
        cover = [point for point, lo, hi in self.feeds.values() if lo <= key <= hi]
        return min(cover) if cover else self.head

    # --- rule 5: the spans ------------------------------------------------------------
    def spans(self, key):
        top = self.trailing(key)
        cuts = sorted(p for p in self.held(key) if p <= top)
        out, floor = [], 0
        for q in cuts:
            if q > floor:
                out.append((floor, q))
            floor = q
        return out

    def seqs_in(self, key, floor, top):
        return [s for s in sorted(self.ent)
                if floor < s <= top and self.ent[s][1] == key]

    # --- rules 6, 7 and 8: what a span keeps ------------------------------------------
    def removal(self, key, floor, top):
        seqs = self.seqs_in(key, floor, top)
        if not seqs:
            return 0, seqs, False
        lo, hi = self.value(key, floor), self.value(key, top)
        need = lo is not hi if (lo is ABSENT or hi is ABSENT) else lo != hi
        return len(seqs) - (1 if need else 0), seqs, need

    def collapse(self, key, floor, top):
        _, seqs, need = self.removal(key, floor, top)
        hi = self.value(key, top)
        keep = seqs[-1] if need else None
        for s in seqs:
            if s != keep:
                del self.ent[s]
        if keep is not None:
            self.ent[keep] = ("del", key, None) if hi is ABSENT else ("set", key, hi)

    # --- rule 9: the budgeted pare ----------------------------------------------------
    def pare(self, budget):
        gone = 0
        while len(self.ent) > budget:
            best = None
            live = sorted({self.ent[s][1] for s in self.ent})
            for key in live:
                for floor, top in self.spans(key):
                    rem, _seqs, _need = self.removal(key, floor, top)
                    if rem <= 0:
                        continue
                    order = (-rem, top, key)
                    if best is None or order < best[0]:
                        best = (order, key, floor, top, rem)
            if best is None:
                break
            _order, key, floor, top, rem = best
            self.collapse(key, floor, top)
            gone += rem
        self.out.append("pare %d %d" % (gone, len(self.ent)))

    # --- the command loop -------------------------------------------------------------
    def point_of(self, name):
        if name in self.marks:
            return self.marks[name]
        return self.feeds[name][0]

    def step(self, line):
        bits = line.split()
        if not bits:
            return
        op = bits[0]
        if op == "cfg":
            self.keys = int(bits[1])
        elif op == "set":
            self.head += 1
            self.ent[self.head] = ("set", int(bits[1]), int(bits[2]))
        elif op == "add":
            self.head += 1
            self.ent[self.head] = ("add", int(bits[1]), int(bits[2]))
        elif op == "del":
            self.head += 1
            self.ent[self.head] = ("del", int(bits[1]), None)
        elif op == "mark":
            self.marks[bits[1]] = self.head
        elif op == "unmark":
            del self.marks[bits[1]]
        elif op == "feed":
            self.feeds[bits[1]] = [self.head, int(bits[2]), int(bits[3])]
        elif op == "ack":
            want = int(bits[2])
            rec = self.feeds[bits[1]]
            if want > rec[0] and want <= self.head:
                rec[0] = want
        elif op == "close":
            del self.feeds[bits[1]]
        elif op == "read":
            v = self.value(int(bits[2]), self.point_of(bits[1]))
            self.out.append("val %s %s %s" % (bits[1], bits[2], "-" if v is ABSENT else v))
        elif op == "pare":
            self.pare(int(bits[1]))
        else:
            raise ValueError(op)

    def report(self):
        self.out.append("log %d" % len(self.ent))
        byk = {}
        for seq in sorted(self.ent):
            kind, key, arg = self.ent[seq]
            item = "%dd" % seq if kind == "del" else "%d%s%d" % (seq, "s" if kind == "set" else "a", arg)
            byk.setdefault(key, []).append(item)
        for key in sorted(byk):
            self.out.append("k %d %s" % (key, " ".join(byk[key])))


def run(text):
    m = Slow()
    for line in text.splitlines():
        m.step(line)
    m.report()
    return m.out
