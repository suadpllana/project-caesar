"""A second engine for the same contract, written apart from the one under `/app`.

It is the sealed side's own answer, so it shares nothing with the reference: it reads the
program itself rather than through the shipped reader, holds a name's state in one record
instead of parallel tables, drives extraction from a log of the moments a name entered the
wanted set feeding a heap per bundle rather than by taking the smallest position over the
wanted set at each step, and walks the prune breadth first from a queue rather than depth
first from a stack. The two agree on the frozen answers and on every generated program, which
is what makes a disagreement evidence about a submission rather than about either engine.

The rules it implements, in the order they bite:

  * a unit is loaded once; a part whose claim key is already held is dropped, and the gives
    and uses it would have brought never enter;
  * a part of a unit named in the input list takes a key back from a part that came out of a
    bundle, and the displaced part's gives and uses leave, before the new part enters;
  * a name is wanted when a kept part uses it strongly or a loaded unit spares it, and no kept
    part gives it strongly; a weak give never settles a name, a weak use never wants one;
  * a bundle gives up its first member, in member order, that strongly gives a wanted name,
    and is scanned again from the first member after each take; a group of bundles is scanned
    again from its first bundle while a pass over it takes anything;
  * a take is never unsaid, whatever leaves the table afterwards;
  * strong gives are kept in arrival order and the first binds; a second prints and changes
    nothing; when the first leaves, the next binds silently;
  * a name nothing gives and something spares is placed at the largest size spared, against
    the first unit in load order that spared it at that size;
  * the prune keeps what the roots reach through strong uses, and a name whose part it drops
    binds to nothing.
"""
import heapq
from collections import deque


class P:
    __slots__ = ("unit", "idx", "size", "key", "gives", "uses")

    def __init__(self, unit, idx, size, key):
        self.unit = unit
        self.idx = idx
        self.size = size
        self.key = key
        self.gives = []
        self.uses = []


class U:
    __slots__ = ("name", "parts", "spares")

    def __init__(self, name):
        self.name = name
        self.parts = []
        self.spares = []


class Slot:
    """Everything one name has collected. One record rather than four tables."""

    __slots__ = ("firm", "soft", "need", "spare")

    def __init__(self):
        self.firm = []
        self.soft = []
        self.need = 0
        self.spare = []


class Row:
    """One bundle inside a link item, with the index that never changes and the heap that does."""

    __slots__ = ("name", "mem", "idx", "heap", "taken", "at", "seen")

    def __init__(self, name, mem, units):
        self.name = name
        self.mem = mem
        self.idx = {}
        for pos, who in enumerate(mem):
            u = units.get(who)
            if u is None:
                continue
            for p in u.parts:
                for nm, strong in p.gives:
                    if not strong:
                        continue
                    row = self.idx.get(nm)
                    if row is None:
                        self.idx[nm] = [pos]
                    elif row[-1] != pos:
                        row.append(pos)
        self.heap = []
        self.taken = set()
        self.at = {}
        self.seen = 0


class Mod:
    def __init__(self):
        self.units = {}
        self.bundles = {}
        self.roots = []
        self.holds = []
        self.out = []
        self.cur = None
        self.slot = {}
        self.want = set()
        self.fresh = []
        self.parts = {}
        self.owner = {}
        self.fixed = set()
        self.loaded = set()
        self.order = 0
        self.set = {}
        self.live = set()
        self.lit = set()
        self.ran = False

    # --- the name records -------------------------------------------------------------

    def get(self, nm):
        s = self.slot.get(nm)
        if s is None:
            s = self.slot[nm] = Slot()
        return s

    def touch(self, nm):
        s = self.slot.get(nm)
        if s is None:
            return
        on = not s.firm and (s.need > 0 or s.spare)
        if on:
            if nm not in self.want:
                self.want.add(nm)
                self.fresh.append(nm)
        else:
            self.want.discard(nm)

    def arrive(self, p):
        for nm, strong in p.gives:
            s = self.get(nm)
            if strong:
                if s.firm:
                    self.out.append("dup %s %s" % (nm, p.unit))
                s.firm.append(p)
            else:
                s.soft.append(p)
            self.touch(nm)
        for nm, strong in p.uses:
            if strong:
                s = self.get(nm)
                s.need += 1
                self.touch(nm)

    def depart(self, p):
        for nm, strong in p.gives:
            s = self.get(nm)
            row = s.firm if strong else s.soft
            for i in range(len(row)):
                if row[i] is p:
                    del row[i]
                    break
            self.touch(nm)
        for nm, strong in p.uses:
            if strong:
                s = self.get(nm)
                s.need -= 1
                self.touch(nm)

    def stands(self, nm):
        s = self.slot.get(nm)
        if s is None:
            return None
        if s.firm:
            return s.firm[0]
        if s.soft:
            return s.soft[0]
        return None

    # --- loading ----------------------------------------------------------------------

    def load(self, who, direct):
        u = self.units.get(who)
        if u is None or who in self.loaded:
            return
        self.loaded.add(who)
        self.order += 1
        if direct:
            for p in u.parts:
                if p.key is None or p.key not in self.owner or p.key in self.fixed:
                    continue
                old = self.parts.pop(self.owner[p.key])
                del self.owner[p.key]
                self.depart(old)
        for p in u.parts:
            if p.key is not None:
                if p.key in self.owner:
                    continue
                self.owner[p.key] = (p.unit, p.idx)
                if direct:
                    self.fixed.add(p.key)
            self.parts[(p.unit, p.idx)] = p
            self.arrive(p)
        for nm, size in u.spares:
            self.get(nm).spare.append((size, self.order, u.name))
            self.touch(nm)

    # --- extraction -------------------------------------------------------------------

    def offer(self, row, nm):
        """Push this bundle's first member that gives nm and has not been taken."""
        run = row.idx.get(nm)
        if not run:
            return
        i = row.at.get(nm, 0)
        while i < len(run) and run[i] in row.taken:
            i += 1
        row.at[nm] = i
        if i < len(run):
            heapq.heappush(row.heap, (run[i], nm))

    def ahead(self, row):
        while row.seen < len(self.fresh):
            self.offer(row, self.fresh[row.seen])
            row.seen += 1
        while row.heap:
            pos, nm = row.heap[0]
            if pos in row.taken:
                heapq.heappop(row.heap)
                self.offer(row, nm)
                continue
            if nm not in self.want:
                heapq.heappop(row.heap)
                continue
            return pos
        return None

    def scan(self, bundles):
        board = [Row(b, self.bundles.get(b, ()), self.units) for b in bundles]
        while True:
            moved = False
            for row in board:
                while True:
                    pos = self.ahead(row)
                    if pos is None:
                        break
                    row.taken.add(pos)
                    who = row.mem[pos]
                    if who in self.loaded:
                        continue
                    self.out.append("take %s %s" % (row.name, who))
                    self.load(who, False)
                    moved = True
            if not moved:
                return

    # --- placement and the prune ------------------------------------------------------

    def settle(self):
        for nm, s in self.slot.items():
            if not s.spare or s.firm or s.soft:
                continue
            pick = None
            for size, order, who in s.spare:
                if pick is None or size > pick[0] or (size == pick[0] and order < pick[1]):
                    pick = (size, order, who)
            self.set[nm] = (pick[2], pick[0])

    def walk(self):
        queue = deque()
        for nm in self.roots:
            self.meet(nm, queue)
        for spot in self.holds:
            if spot in self.parts and spot not in self.live:
                self.live.add(spot)
                queue.append(self.parts[spot])
        while queue:
            p = queue.popleft()
            for nm, strong in p.uses:
                if strong:
                    self.meet(nm, queue)

    def meet(self, nm, queue):
        p = self.stands(nm)
        if p is not None:
            spot = (p.unit, p.idx)
            if spot not in self.live:
                self.live.add(spot)
                queue.append(p)
        elif nm in self.set:
            self.lit.add(nm)

    # --- the ops ----------------------------------------------------------------------

    def items(self, words):
        out = []
        i = 0
        while i < len(words):
            w = words[i]
            if w == "(":
                pack = []
                i += 1
                while i < len(words) and words[i] != ")":
                    pack.append(words[i])
                    i += 1
                out.append(("g", tuple(pack)))
            elif w in self.bundles:
                out.append(("b", w))
            else:
                out.append(("u", w))
            i += 1
        return out

    def bulk(self, name, shape, n, arg):
        if shape != "chain":
            return
        mem = []
        for i in range(n):
            who = "%s%d" % (name, i)
            u = U(who)
            self.units[who] = u
            one = P(who, 0, 8 + i % 5, None)
            one.gives.append(("%sx%d" % (name, i), True))
            far = i + arg
            if far < n:
                one.uses.append(("%sx%d" % (name, far), True))
            u.parts.append(one)
            two = P(who, 1, 3 + i % 7, "%sk%d" % (name, i % 256))
            two.gives.append(("%sy%d" % (name, i), True))
            u.parts.append(two)
            mem.append(who)
        self.cur = None
        self.bundles[name] = tuple(mem)

    def run(self, words):
        self.ran = True
        for kind, what in self.items(words):
            if kind == "u":
                self.load(what, True)
            elif kind == "b":
                self.scan((what,))
            else:
                self.scan(what)
        self.settle()
        self.walk()

    def ask(self, nm):
        if not self.ran:
            self.out.append("at %s none" % nm)
            return
        p = self.stands(nm)
        if p is not None:
            if (p.unit, p.idx) in self.live:
                self.out.append("at %s %s %d" % (nm, p.unit, p.idx))
            else:
                self.out.append("at %s none" % nm)
        elif nm in self.lit:
            who, size = self.set[nm]
            self.out.append("at %s spare %s %d" % (nm, who, size))
        else:
            self.out.append("at %s none" % nm)

    def pic(self):
        if not self.ran:
            self.out.append("img 0 0")
            return
        total = 0
        for spot in self.live:
            total += self.parts[spot].size
        for nm in self.lit:
            total += self.set[nm][1]
        self.out.append("img %d %d" % (len(self.live) + len(self.lit), total))


def expect(lines):
    """The trace the contract says a program prints."""
    m = Mod()
    for line in lines:
        w = line.split()
        if not w:
            continue
        op = w[0]
        if op == "u":
            m.cur = U(w[1])
            m.units[w[1]] = m.cur
        elif op == "p":
            m.cur.parts.append(P(m.cur.name, len(m.cur.parts), int(w[1]),
                                 None if w[2] == "-" else w[2]))
        elif op == "g":
            m.cur.parts[-1].gives.append((w[1], w[2] == "s"))
        elif op == "r":
            m.cur.parts[-1].uses.append((w[1], w[2] == "s"))
        elif op == "t":
            m.cur.spares.append((w[1], int(w[2])))
        elif op == "b":
            m.bundles[w[1]] = tuple(w[2:])
        elif op == "bulk":
            m.bulk(w[1], w[2], int(w[3]), int(w[4]))
        elif op == "root":
            m.roots.append(w[1])
        elif op == "hold":
            m.holds.append((w[1], int(w[2])))
        elif op == "link":
            m.run(w[1:])
        elif op == "at":
            m.ask(w[1])
        elif op == "img":
            m.pic()
    return m.out
