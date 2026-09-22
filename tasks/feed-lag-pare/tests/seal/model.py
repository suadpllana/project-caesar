"""What a program is supposed to print.

Written apart from the reference under `solution/`, against the same contract, so that a
trace is graded by two implementations that agree rather than by one that is echoed back.
Where the reference folds values forward and carries a pair heap across commands, this one
composes each stretch into a single effect, keeps no heap, and picks the next collapse by
sorting. The rules the two share are the contract; nothing else is.

An effect is what a run of entries does to whatever value stood before it:

    ("nop",)      nothing happened here
    ("add", n)    the value went up by n, and an absent key became n
    ("set", v)    the value is v, whatever it was
    ("del",)      the key is absent, whatever it was

Composition is associative, which is the whole reason for the shape: a stretch's effect is
the composition of its entries' effects, the value at its top is that effect applied to the
value at its floor, and merging two stretches is composing their effects.
"""
import bisect

GONE = "gone"


def blend(one, two):
    """The effect of `one` followed by `two`."""
    if two[0] == "nop":
        return one
    if two[0] in ("set", "del"):
        return two
    n = two[1]
    if one[0] == "nop":
        return ("add", n)
    if one[0] == "add":
        return ("add", one[1] + n)
    if one[0] == "set":
        return ("set", one[1] + n)
    return ("set", n)


def apply(eff, before):
    if eff[0] == "nop":
        return before
    if eff[0] == "set":
        return eff[1]
    if eff[0] == "del":
        return GONE
    return eff[1] if before is GONE else before + eff[1]


def effect_of(kind, arg):
    if kind == "set":
        return ("set", arg)
    if kind == "add":
        return ("add", arg)
    return ("del",)


class Model:
    def __init__(self):
        self.ent = {}
        self.rows = {}
        self.head = 0
        self.marks = {}
        self.feeds = {}
        self.cache = {}
        self.stale = set()
        self.out = []

    # --- the log ----------------------------------------------------------------------
    def add_entry(self, kind, key, arg):
        self.head += 1
        self.ent[self.head] = (kind, key, arg)
        self.rows.setdefault(key, []).append(self.head)
        self.stale.add(key)

    def erase(self, seq):
        key = self.ent.pop(seq)[1]
        row = self.rows[key]
        del row[bisect.bisect_left(row, seq)]
        if not row:
            del self.rows[key]
        self.stale.add(key)

    def slice(self, key, floor, top):
        row = self.rows.get(key)
        if not row:
            return ()
        return row[bisect.bisect_right(row, floor):bisect.bisect_right(row, top)]

    # --- pins -------------------------------------------------------------------------
    def edges(self, key):
        seen = {self.head}
        seen.update(self.marks.values())
        for at, lo, hi in self.feeds.values():
            if lo <= key <= hi:
                seen.add(at)
        return seen

    def limit(self, key):
        low = None
        for at, lo, hi in self.feeds.values():
            if lo <= key <= hi and (low is None or at < low):
                low = at
        return self.head if low is None else low

    # --- the stretches of one key -----------------------------------------------------
    def stretches(self, key):
        """(floor, top, count, last, value below, value at top) for every stretch holding
        an entry, from the bottom of the log up to the key's trailing point."""
        if key not in self.stale and key in self.cache:
            return self.cache[key]
        top = self.limit(key)
        cuts = sorted(e for e in self.edges(key) if 0 < e <= top)
        row = self.rows.get(key, [])
        found = []
        standing = GONE
        floor = 0
        seen = 0
        for cut in cuts:
            run = ("nop",)
            count = 0
            last = None
            while seen < len(row) and row[seen] <= cut:
                kind, _k, arg = self.ent[row[seen]]
                run = blend(run, effect_of(kind, arg))
                last = row[seen]
                count += 1
                seen += 1
            after = apply(run, standing)
            if count:
                found.append((floor, cut, count, last, standing, after))
            standing = after
            floor = cut
        self.cache[key] = found
        self.stale.discard(key)
        return found

    # --- what a collapse is worth, and what it does -----------------------------------
    @staticmethod
    def worth(item):
        _floor, _cut, count, _last, below, above = item
        return count - (0 if below == above else 1)

    def take(self, key, item):
        floor, cut, _count, last, below, above = item
        seqs = self.slice(key, floor, cut)
        keep = last if below != above else None
        for seq in seqs:
            if seq != keep:
                self.erase(seq)
        if keep is not None:
            if above is GONE:
                self.ent[keep] = ("del", key, None)
            else:
                self.ent[keep] = ("set", key, above)
        self.stale.add(key)
        return len(seqs) - (0 if keep is None else 1)

    # --- the budgeted pare ------------------------------------------------------------
    def pare(self, budget):
        gone = 0
        while len(self.ent) > budget:
            board = []
            for key in self.rows:
                for item in self.stretches(key):
                    won = self.worth(item)
                    if won > 0:
                        board.append((-won, item[1], key, item))
            if not board:
                break
            board.sort(key=lambda row: (row[0], row[1], row[2]))
            for _won, _cut, key, item in board:
                if len(self.ent) <= budget:
                    break
                gone += self.take(key, item)
        self.out.append("pare %d %d" % (gone, len(self.ent)))

    # --- commands ---------------------------------------------------------------------
    def where(self, name):
        if name in self.marks:
            return self.marks[name]
        return self.feeds[name][0]

    def value_at(self, key, point):
        standing = GONE
        seqs = self.slice(key, 0, point)
        for seq in seqs:
            kind, _k, arg = self.ent[seq]
            standing = apply(effect_of(kind, arg), standing)
        return standing

    def command(self, line):
        bits = line.split()
        if not bits:
            return
        op = bits[0]
        if op == "set":
            self.add_entry("set", int(bits[1]), int(bits[2]))
        elif op == "add":
            self.add_entry("add", int(bits[1]), int(bits[2]))
        elif op == "del":
            self.add_entry("del", int(bits[1]), None)
        elif op == "mark":
            self.marks[bits[1]] = self.head
            self.stale.update(self.rows)
        elif op == "unmark":
            del self.marks[bits[1]]
            self.stale.update(self.rows)
        elif op == "feed":
            self.feeds[bits[1]] = (self.head, int(bits[2]), int(bits[3]))
            self.touch(int(bits[2]), int(bits[3]))
        elif op == "ack":
            at, lo, hi = self.feeds[bits[1]]
            want = int(bits[2])
            if want > at and want <= self.head:
                self.feeds[bits[1]] = (want, lo, hi)
                self.touch(lo, hi)
        elif op == "close":
            _at, lo, hi = self.feeds.pop(bits[1])
            self.touch(lo, hi)
        elif op == "read":
            key = int(bits[2])
            got = self.value_at(key, self.where(bits[1]))
            self.out.append("val %s %d %s" % (bits[1], key, "-" if got is GONE else got))
        elif op == "pare":
            self.pare(int(bits[1]))
        else:
            raise ValueError(line)

    def touch(self, lo, hi):
        for key in self.rows:
            if lo <= key <= hi:
                self.stale.add(key)

    def finish(self):
        self.out.append("log %d" % len(self.ent))
        shown = {}
        for seq in sorted(self.ent):
            kind, key, arg = self.ent[seq]
            if kind == "del":
                shown.setdefault(key, []).append("%dd" % seq)
            else:
                shown.setdefault(key, []).append(
                    "%d%s%d" % (seq, "s" if kind == "set" else "a", arg))
        for key in sorted(shown):
            self.out.append("k %d %s" % (key, " ".join(shown[key])))


def expect(lines):
    """The trace a correct service prints for this program."""
    box = Model()
    for line in lines:
        box.command(line)
    box.finish()
    return box.out
