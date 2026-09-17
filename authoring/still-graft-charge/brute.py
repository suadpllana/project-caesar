"""Definitional semantics of the ledger, written for clarity and not for speed.

Nothing here is shipped. This file is the arbiter the two fast implementations - the sealed
model under tests/seal/ and the reference under solution/ - are checked against on small
programs, because it says what the rules mean in the plainest way available: every holder
question is answered by looking at every line and every still, and every charge by walking
every block that was ever written.

It is also the naive family the execution limit is aimed at: correct, and hopeless at the
size the graded programs run at.
"""


class Block:
    __slots__ = ("num", "size")

    def __init__(self, num, size):
        self.num = num
        self.size = size


class Line:
    __slots__ = ("cap", "origin", "stills", "head")

    def __init__(self):
        self.cap = None
        self.origin = None
        self.stills = []
        self.head = {}


class Still:
    __slots__ = ("owner", "held")

    def __init__(self, owner, held):
        self.owner = owner
        self.held = held


class Store:
    def __init__(self):
        self.lines = {}
        self.stills = {}
        self.blocks = []
        self.nput = 0
        self.out = []

    # --- the two questions everything else is phrased in ------------------------------

    def holders(self, block):
        """Every line holding this block, by its head or by one of its stills."""
        who = set()
        for name, line in self.lines.items():
            if block in line.head.values():
                who.add(name)
                continue
            for s in line.stills:
                if block in self.stills[s].held.values():
                    who.add(name)
                    break
        return who

    def charge(self, name):
        """The blocks this line holds that no other line holds."""
        total = 0
        for block in self.blocks:
            who = self.holders(block)
            if who == {name}:
                total += block.size
        return total

    # --- the ops ----------------------------------------------------------------------

    def op_line(self, name):
        self.lines[name] = Line()

    def op_cap(self, name, size):
        self.lines[name].cap = size

    def op_put(self, name, lo, hi, size):
        line = self.lines[name]
        cells = range(lo, hi + 1)
        keep = dict(line.head)
        fresh = [Block(0, size) for _ in cells]
        self.blocks.extend(fresh)
        for cell, block in zip(cells, fresh):
            line.head[cell] = block
        if line.cap is not None and self.charge(name) > line.cap:
            line.head = keep
            del self.blocks[len(self.blocks) - len(fresh):]
            self.out.append("full %s" % name)
            return
        self.nput += 1
        for block in fresh:
            block.num = self.nput

    def op_cut(self, name, lo, hi):
        line = self.lines[name]
        for cell in range(lo, hi + 1):
            line.head.pop(cell, None)

    def op_still(self, name, still):
        line = self.lines[name]
        self.stills[still] = Still(name, dict(line.head))
        line.stills.append(still)

    def op_graft(self, still, name):
        line = Line()
        line.origin = still
        line.head = dict(self.stills[still].held)
        self.lines[name] = line

    def op_lift(self, name):
        line = self.lines[name]
        if line.origin is None:
            return
        still = line.origin
        up = self.stills[still].owner
        above = self.lines[up]
        cut = above.stills.index(still) + 1
        moved = above.stills[:cut]
        above.stills = above.stills[cut:]
        line.stills = moved + line.stills
        for one in moved:
            self.stills[one].owner = name
        line.origin = above.origin
        above.origin = still

    def op_drop(self, still):
        for line in self.lines.values():
            if line.origin == still:
                self.out.append("busy %s" % still)
                return
        was = list(self.stills[still].held.values())
        owner = self.stills[still].owner
        self.lines[owner].stills.remove(still)
        del self.stills[still]
        freed = 0
        for block in was:
            if not self.holders(block):
                freed += block.size
        self.out.append("free %s %d" % (still, freed))

    def op_ask(self, name):
        self.out.append("charge %s %d" % (name, self.charge(name)))

    def op_at(self, name, cell):
        block = self.lines[name].head.get(cell)
        self.out.append("at %s %d %s" % (name, cell, block.num if block else "-"))


def ex(store, w):
    op = w[0]
    if op == "line":
        store.op_line(w[1])
    elif op == "cap":
        store.op_cap(w[1], int(w[2]))
    elif op == "put":
        store.op_put(w[1], int(w[2]), int(w[3]), int(w[4]))
    elif op == "cut":
        store.op_cut(w[1], int(w[2]), int(w[3]))
    elif op == "still":
        store.op_still(w[1], w[2])
    elif op == "graft":
        store.op_graft(w[1], w[2])
    elif op == "lift":
        store.op_lift(w[1])
    elif op == "drop":
        store.op_drop(w[1])
    elif op == "ask":
        store.op_ask(w[1])
    elif op == "at":
        store.op_at(w[1], int(w[2]))
    else:
        raise ValueError(op)


def expect(lines):
    store = Store()
    for line in lines:
        ex(store, tuple(line.split()))
    return store.out
