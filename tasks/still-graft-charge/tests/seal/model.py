"""The sealed model: a second implementation of the ledger, written apart from the reference.

It settles the same nine decisions, and every part that decides one is built apart:

  * holders are read off a compressed run list per line - the still indices taken on that
    line, cut into segments by owner - rather than by counting indices in a window and naming
    the handful a lift moved;
  * the charge of a line is a dict of the blocks it holds alone, so the total is a sum kept
    beside the membership, rather than a single running number;
  * a cap is decided by arithmetic before anything is written - the charge the line has, plus
    what the put adds, less the blocks of its own the put lets go of - rather than by letting
    the write stand and taking it back when it does not fit;
  * a lift re-settles only the blocks the moved stills were holding, found through their own
    windows, rather than every block with an entry on the lines those stills were taken on.

Both implementations are checked against `authoring/still-graft-charge/brute.py`, which says
what the rules mean in the plainest possible way and is far too slow to ship.
"""
from bisect import bisect_left, bisect_right


class Blk:
    __slots__ = ("num", "size", "at", "sole")

    def __init__(self, size):
        self.num = 0
        self.size = size
        self.at = []
        self.sole = None


class Place:
    __slots__ = ("line", "cell", "blk", "born", "died")

    def __init__(self, line, cell, blk, born):
        self.line = line
        self.cell = cell
        self.blk = blk
        self.born = born
        self.died = None


class Line:
    __slots__ = ("cap", "origin", "stills", "hist", "seq", "segs", "mine", "total")

    def __init__(self):
        self.cap = None
        self.origin = None
        self.stills = []          # the stills this line owns, oldest first
        self.hist = {}            # cell -> [Place, ...] in the order they were laid down
        self.seq = []             # (index, owner) for the live stills taken on this line
        self.segs = []            # seq compressed into (lo, hi, owner) runs
        self.mine = {}            # id(blk) -> size, for the blocks this line holds alone
        self.total = 0


class Still:
    __slots__ = ("on", "idx")

    def __init__(self, on, idx):
        self.on = on
        self.idx = idx


class Ledger:
    def __init__(self):
        self.lines = {}
        self.stills = {}
        self.out = []
        self.nput = 0
        self.g = 0

    # --- the map ----------------------------------------------------------------------

    def open_at(self, line, cell):
        """The placement a head has at this cell, or None."""
        chain = line.hist.get(cell)
        if not chain:
            return None
        last = chain[-1]
        return last if last.died is None else None

    def under(self, line, cell, idx):
        """The placement a still at this index sees at this cell, or None."""
        chain = line.hist.get(cell)
        if not chain:
            return None
        pos = bisect_right([p.born for p in chain], idx) - 1
        if pos < 0:
            return None
        p = chain[pos]
        if p.died is not None and idx >= p.died:
            return None
        return p

    def spans(self, still):
        """Every (cell, block) a still is holding, through the chains of its own line."""
        rec = self.stills[still]
        src = self.lines[rec.on]
        out = []
        for cell in src.hist:
            p = self.under(src, cell, rec.idx)
            if p is not None:
                out.append((cell, p.blk))
        return out

    # --- who holds a block ------------------------------------------------------------

    def recut(self, line):
        """Compress the live stills taken on a line into runs of one owner."""
        segs = []
        for idx, owner in line.seq:
            if segs and segs[-1][0] == owner:
                segs[-1][1].append(idx)
            else:
                segs.append((owner, [idx]))
        line.segs = segs

    def owners(self, name, lo, hi):
        """The lines owning a still taken on `name` with an index in [lo, hi)."""
        out = set()
        for owner, idxs in self.lines[name].segs:
            if owner in out or idxs[-1] < lo or idxs[0] >= hi:
                continue
            if bisect_left(idxs, lo) < bisect_right(idxs, hi - 1):
                out.add(owner)
        return out

    def holders(self, blk):
        out = set()
        for p in blk.at:
            if p.died is None:
                out.add(p.line)
                hi = self.g
            else:
                hi = p.died
            if hi > p.born:
                out |= self.owners(p.line, p.born, hi)
        return out

    def rests(self, blk, who):
        """Put a block's size on the line holding it alone, and take it off any other."""
        one = next(iter(who)) if len(who) == 1 else None
        if one == blk.sole:
            return
        if blk.sole is not None:
            was = self.lines[blk.sole]
            was.total -= was.mine.pop(id(blk))
        if one is not None:
            now = self.lines[one]
            now.mine[id(blk)] = blk.size
            now.total += blk.size
        blk.sole = one

    def resettle(self, blocks):
        for blk in blocks:
            self.rests(blk, self.holders(blk))

    # --- the ops ----------------------------------------------------------------------

    def op_line(self, name):
        self.lines[name] = Line()

    def op_cap(self, name, size):
        self.lines[name].cap = size

    def lay(self, name, cell, blk):
        p = Place(name, cell, blk, self.g)
        self.lines[name].hist.setdefault(cell, []).append(p)
        blk.at.append(p)
        return p

    def op_put(self, name, lo, hi, size):
        line = self.lines[name]
        cells = range(lo, hi + 1)
        if line.cap is not None:
            after = line.total + len(cells) * size
            for cell in cells:
                p = self.open_at(line, cell)
                if p is None or p.blk.sole != name:
                    continue
                # the block goes off this line's books unless one of its own stills is
                # still holding it once the window closes here
                if name not in self.owners(p.line, p.born, self.g):
                    after -= p.blk.size
            if after > line.cap:
                self.out.append("full %s" % name)
                return
        self.nput += 1
        shut = []
        made = []
        for cell in cells:
            p = self.open_at(line, cell)
            if p is not None:
                p.died = self.g
                shut.append(p.blk)
            blk = Blk(size)
            blk.num = self.nput
            self.lay(name, cell, blk)
            made.append(blk)
        self.resettle(made)
        self.resettle(shut)

    def op_cut(self, name, lo, hi):
        line = self.lines[name]
        shut = []
        for cell in range(lo, hi + 1):
            p = self.open_at(line, cell)
            if p is not None:
                p.died = self.g
                shut.append(p.blk)
        self.resettle(shut)

    def op_still(self, name, still):
        line = self.lines[name]
        self.stills[still] = Still(name, self.g)
        line.seq.append((self.g, name))
        self.recut(line)
        line.stills.append(still)
        self.g += 1

    def op_graft(self, still, name):
        line = Line()
        line.origin = still
        self.lines[name] = line
        got = self.spans(still)
        for cell, blk in got:
            self.lay(name, cell, blk)
        self.resettle([blk for _cell, blk in got])

    def op_lift(self, name):
        line = self.lines[name]
        if line.origin is None:
            return
        still = line.origin
        up = self.owner_of(still)
        above = self.lines[up]
        cut = above.stills.index(still) + 1
        moved = above.stills[:cut]
        above.stills = above.stills[cut:]
        line.stills = moved + line.stills
        stirred = []
        for one in moved:
            stirred.extend(blk for _cell, blk in self.spans(one))
        for one in moved:
            rec = self.stills[one]
            src = self.lines[rec.on]
            src.seq = [(i, name if i == rec.idx else o) for (i, o) in src.seq]
            self.recut(src)
        line.origin = above.origin
        above.origin = still
        self.resettle(stirred)

    def owner_of(self, still):
        for name, line in self.lines.items():
            if still in line.stills:
                return name
        raise KeyError(still)

    def op_drop(self, still):
        for line in self.lines.values():
            if line.origin == still:
                self.out.append("busy %s" % still)
                return
        rec = self.stills[still]
        was = [blk for _cell, blk in self.spans(still)]
        owner = self.owner_of(still)
        self.lines[owner].stills.remove(still)
        src = self.lines[rec.on]
        src.seq = [(i, o) for (i, o) in src.seq if i != rec.idx]
        self.recut(src)
        del self.stills[still]
        freed = 0
        for blk in was:
            who = self.holders(blk)
            self.rests(blk, who)
            if not who:
                freed += blk.size
        self.out.append("free %s %d" % (still, freed))

    def op_ask(self, name):
        self.out.append("charge %s %d" % (name, self.lines[name].total))

    def op_at(self, name, cell):
        p = self.open_at(self.lines[name], cell)
        self.out.append("at %s %d %s" % (name, cell, p.blk.num if p else "-"))


def ex(led, w):
    op = w[0]
    if op == "line":
        led.op_line(w[1])
    elif op == "cap":
        led.op_cap(w[1], int(w[2]))
    elif op == "put":
        led.op_put(w[1], int(w[2]), int(w[3]), int(w[4]))
    elif op == "cut":
        led.op_cut(w[1], int(w[2]), int(w[3]))
    elif op == "still":
        led.op_still(w[1], w[2])
    elif op == "graft":
        led.op_graft(w[1], w[2])
    elif op == "lift":
        led.op_lift(w[1])
    elif op == "drop":
        led.op_drop(w[1])
    elif op == "ask":
        led.op_ask(w[1])
    elif op == "at":
        led.op_at(w[1], int(w[2]))
    else:
        raise ValueError(op)


def expect(lines):
    led = Ledger()
    for line in lines:
        ex(led, tuple(line.split()))
    return led.out
