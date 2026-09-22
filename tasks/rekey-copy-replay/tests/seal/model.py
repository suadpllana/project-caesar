"""Sealed model of the rebuild.

Written before the reference and from the frozen contract alone, so that agreement between
the two is evidence rather than a shared bug. The structures here are deliberately not the
reference's: source keys live in one bisect-maintained list, chunk ranges are searched with
bisect, and the rows set aside for a new key are a sorted list per key.

The contract, in the order a program exercises it:

  1  a chunk takes the smallest CHUNK source keys standing above the cursor, as the source
     stands at that moment; the cursor lands on the largest key taken; a chunk that takes
     nothing leaves the cursor where it is and records no range
  2  a chunk that took something records the range (cursor before, cursor after] against the
     journal length standing at that moment, its mark
  3  an entry whose source key is above the cursor is dropped as ahead
  4  an entry at or below the cursor whose position is at most the mark of the range covering
     its key is dropped as seen, because the chunk that carried the key was read later
  5  any other entry is applied
  6  a row's new key is its first two fields; a row the rebuild already knows whose first two
     fields are unchanged is updated where it stands
  7  a row that changes its new key leaves the key the rebuild holds for it, not the key its
     source row would name now
  8  a free new key is taken; a held one sets the arriving row aside
  9  a freed new key goes to the smallest source key set aside for it
 10  a delete reaches the row the rebuild holds, and a delete of a row the rebuild does not
     know reports a miss
 11  the walk offers the keys it took in ascending order, by the same rules as a replay
 12  the closing line counts the rows holding a key, the rows set aside, and totals the third
     field over the rows holding a key only
"""
import bisect


class Model:
    def __init__(self, chunk):
        self.chunk = chunk
        self.src = {}          # source key -> (a, b, c)
        self.keys = []         # source keys, ascending
        self.jrn = []          # entries; position is index + 1
        self.seen_upto = 0     # entries already considered by a play
        self.cur = 0           # the walk's cursor
        self.lo = []           # range lows, ascending
        self.hi = []           # range highs, ascending
        self.mark = []         # the journal length each range was read at
        self.row = {}          # source key -> (a, b, c) as the rebuild holds it
        self.up = {}           # source key -> True when it holds its new key
        self.held = {}         # (a, b) -> the source key holding it
        self.wait = {}         # (a, b) -> source keys set aside for it, ascending
        self.out = []

    # --- the source and its journal -------------------------------------------------

    def write(self, k, a, b, c):
        if k not in self.src:
            bisect.insort(self.keys, k)
        self.src[k] = (a, b, c)
        self.jrn.append(("set", k, a, b, c))

    def erase(self, k):
        if k in self.src:
            del self.src[k]
            i = bisect.bisect_left(self.keys, k)
            del self.keys[i]
        self.jrn.append(("del", k, 0, 0, 0))

    # --- the rebuild ----------------------------------------------------------------

    def _free(self, key):
        """A new key has stopped being held: the smallest row set aside for it takes it."""
        line = self.wait.get(key)
        if not line:
            self.held.pop(key, None)
            return
        k = line.pop(0)
        if not line:
            del self.wait[key]
        self.held[key] = k
        self.up[k] = True
        self.out.append("on %d %d:%d" % (k, key[0], key[1]))

    def _withdraw(self, k):
        """Take a row off whatever it holds or waits for, and report which it was."""
        a, b, _c = self.row[k]
        key = (a, b)
        if self.up[k]:
            self.out.append("off %d %d:%d" % (k, a, b))
            self._free(key)
        else:
            self.out.append("drop %d %d:%d" % (k, a, b))
            line = self.wait.get(key)
            if line is not None:
                line.remove(k)
                if not line:
                    del self.wait[key]

    def _ask(self, k, a, b, c):
        """A row that holds nothing asks for its new key."""
        key = (a, b)
        self.row[k] = (a, b, c)
        if key in self.held:
            self.up[k] = False
            line = self.wait.setdefault(key, [])
            bisect.insort(line, k)
            self.out.append("aside %d %d:%d" % (k, a, b))
        else:
            self.up[k] = True
            self.held[key] = k
            self.out.append("on %d %d:%d" % (k, a, b))

    def offer(self, k, a, b, c):
        if k in self.row:
            a0, b0, _c0 = self.row[k]
            if (a0, b0) == (a, b):
                self.row[k] = (a, b, c)
                self.out.append("same %d %d:%d" % (k, a, b))
                return
            self._withdraw(k)
            del self.row[k]
            del self.up[k]
        self._ask(k, a, b, c)

    def remove(self, k):
        if k not in self.row:
            self.out.append("miss %d" % k)
            return
        self._withdraw(k)
        del self.row[k]
        del self.up[k]

    # --- the walk -------------------------------------------------------------------

    def copy(self):
        i = bisect.bisect_right(self.keys, self.cur)
        taken = self.keys[i:i + self.chunk]
        if not taken:
            self.out.append("chunk 0 %d none" % self.cur)
            return
        mark = len(self.jrn)
        self.lo.append(self.cur)
        self.hi.append(taken[-1])
        self.mark.append(mark)
        self.cur = taken[-1]
        self.out.append("chunk %d %d %d" % (len(taken), self.cur, mark))
        for k in taken:
            a, b, c = self.src[k]
            self.offer(k, a, b, c)

    # --- the replay -----------------------------------------------------------------

    def _mark_for(self, k):
        i = bisect.bisect_left(self.hi, k)
        return self.mark[i]

    def play(self, n):
        stop = min(len(self.jrn), self.seen_upto + n)
        while self.seen_upto < stop:
            p = self.seen_upto + 1
            kind, k, a, b, c = self.jrn[self.seen_upto]
            self.seen_upto += 1
            if k > self.cur:
                self.out.append("entry %d %d ahead" % (p, k))
                continue
            if p <= self._mark_for(k):
                self.out.append("entry %d %d seen" % (p, k))
                continue
            self.out.append("entry %d %d done" % (p, k))
            if kind == "set":
                self.offer(k, a, b, c)
            else:
                self.remove(k)

    def drain(self):
        self.play(len(self.jrn) - self.seen_upto)

    def cut(self):
        while True:
            before = self.cur
            self.copy()
            self.drain()
            if self.cur == before:
                break
        placed = sum(1 for k in self.row if self.up[k])
        aside = len(self.row) - placed
        total = sum(self.row[k][2] for k in self.row if self.up[k])
        self.out.append("end %d %d %d" % (placed, aside, total))


def expect(lines):
    """Run a program, given as a list of instruction lines, and return its printed lines."""
    m = None
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        part = line.split()
        head = part[0]
        if head == "cfg":
            m = Model(int(part[1]))
        elif head == "set":
            m.write(int(part[1]), int(part[2]), int(part[3]), int(part[4]))
        elif head == "del":
            m.erase(int(part[1]))
        elif head == "copy":
            m.copy()
        elif head == "play":
            m.play(int(part[1]))
        elif head == "cut":
            m.cut()
        else:
            raise ValueError("unknown instruction: %s" % head)
    return m.out
