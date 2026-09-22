"""The sealed model: what every graded program must print.

Written apart from the reference under `/app/led/`, from the frozen contract in STATE.md, and
kept in a different shape on purpose. Where the reference carries a key's value as one tuple in
one dict and saves that dict at every mark, this carries the basis and the offset in two dicts;
where the reference walks the close with a for loop over the work, this drives it from an
index and a stack of restore points, and a section that goes is left behind the cursor rather
than taken out of the list.

Both agree with a third, deliberately naive engine (authoring/pin-drift-redo/proto/naive.py,
which re-derives the whole work list on every re-take and after every cut) on the whole graded
population and on tens of thousands of random programs.

The rules, in the order the contract states them:

  1  a transaction takes the number standing at a key the first time one of its ops names it,
     and `cpy` and `raw` name two keys while `bmp` names its whole range
  2  an op whose key has moved since it was taken takes it again before the op runs
  3  the number held at a key is what the transaction's work makes of the numbers it has
     taken, so taking again moves everything derived from that key
  4  a read prints the number held and puts an entry in the work fixing it
  5  a mark cuts: `un` throws away the work from the last standing mark through the end
  6  a condition is recorded and tested only when the transaction closes
  7  the close takes every moved key again, then tests the conditions in work order, each at
     its own position
  8  a condition that fails throws away the work from the last standing mark through itself
     and the testing carries on; with no mark standing the close writes nothing
  9  the close writes the keys the surviving work sets, in ascending order
"""

PUT, ADD, CPY, RAW, FIX, MARK, EQ, GE = range(8)

ARITY = {"cfg": 1, "tx": 1, "rd": 2, "put": 3, "add": 3, "cpy": 3, "raw": 3,
         "bmp": 4, "chk": 3, "lim": 3, "mk": 1, "un": 1, "fin": 1, "drp": 1}

NAMES = {"rd": (2,), "put": (2,), "add": (2,), "cpy": (2, 3), "raw": (2, 3),
         "chk": (2,), "lim": (2,)}

FIXED = -1


class Deal:
    """One open transaction."""

    def __init__(self, num):
        self.num = num
        self.took = {}          # key -> the number taken for it
        self.base = {}          # key -> the key its number is owed to, or FIXED
        self.off = {}           # key -> the offset on that basis, or the fixed number
        self.work = []
        self.rest = []          # (length of work, base copy, off copy, wrote copy)
        self.wrote = set()

    def name(self, store, keys):
        for k in keys:
            if k in self.took:
                if self.took[k] != store[k]:
                    self.took[k] = store[k]
            else:
                self.took[k] = store[k]
                self.base[k] = k
                self.off[k] = 0

    def holds(self, k):
        if self.base[k] == FIXED:
            return self.off[k]
        return self.took[self.base[k]] + self.off[k]

    def fix(self, k, n):
        self.base[k] = FIXED
        self.off[k] = n

    def shift(self, k, n):
        self.off[k] = self.off[k] + n

    def like(self, k, j):
        self.base[k] = self.base[j]
        self.off[k] = self.off[j]

    def owe(self, k, j):
        self.base[k] = j
        self.off[k] = 0


def keys_named(op):
    if op[0] == "bmp":
        return range(op[2], op[3])
    return [op[i] for i in NAMES.get(op[0], ())]


def expect(lines):
    """The lines a correct engine prints for this program."""
    said = []
    store = {}
    live = {}
    for line in lines:
        bits = line.split()
        if not bits:
            continue
        kind = bits[0]
        arg = [int(b) for b in bits[1:1 + ARITY[kind]]]
        if kind == "cfg":
            store = dict.fromkeys(range(arg[0]), 0)
            continue
        if kind == "tx":
            live[arg[0]] = Deal(arg[0])
            continue
        d = live[arg[0]]
        d.name(store, keys_named([kind] + arg))
        if kind == "rd":
            k = arg[1]
            v = d.holds(k)
            said.append("rd %d %d %d" % (d.num, k, v))
            d.work.append((FIX, k, v))
            d.fix(k, v)
        elif kind == "put":
            d.work.append((PUT, arg[1], arg[2]))
            d.fix(arg[1], arg[2])
            d.wrote.add(arg[1])
        elif kind == "add":
            d.work.append((ADD, arg[1], arg[2]))
            d.shift(arg[1], arg[2])
            d.wrote.add(arg[1])
        elif kind == "cpy":
            d.work.append((CPY, arg[1], arg[2]))
            d.like(arg[1], arg[2])
            d.wrote.add(arg[1])
        elif kind == "raw":
            d.work.append((RAW, arg[1], arg[2]))
            d.owe(arg[1], arg[2])
            d.wrote.add(arg[1])
        elif kind == "bmp":
            for k in range(arg[1], arg[2]):
                d.work.append((ADD, k, arg[3]))
                d.shift(k, arg[3])
                d.wrote.add(k)
        elif kind == "chk":
            d.work.append((EQ, arg[1], arg[2]))
        elif kind == "lim":
            d.work.append((GE, arg[1], arg[2]))
        elif kind == "mk":
            d.rest.append((len(d.work), dict(d.base), dict(d.off), set(d.wrote)))
            d.work.append((MARK, 0, 0))
        elif kind == "un":
            undo(d)
        elif kind == "drp":
            del live[arg[0]]
        elif kind == "fin":
            said.append(shut(d, store))
            del live[arg[0]]
    return said


def undo(d):
    if d.rest:
        back, base, off, wrote = d.rest.pop()
        del d.work[back:]
        d.base, d.off, d.wrote = base, off, wrote
    else:
        d.work = []
        d.base, d.off, d.wrote = {}, {}, set()
    for k in d.took:
        if k not in d.base:
            d.base[k] = k
            d.off[k] = 0


def shut(d, store):
    for k in d.took:
        if d.took[k] != store[k]:
            d.took[k] = store[k]
    took = dict(d.took)
    now = dict(took)
    wrote = set()
    stack = []
    at = 0
    work = d.work
    while at < len(work):
        tag, one, two = work[at]
        if tag == PUT:
            now[one] = two
            wrote.add(one)
        elif tag == ADD:
            now[one] = now[one] + two
            wrote.add(one)
        elif tag == CPY:
            now[one] = now[two]
            wrote.add(one)
        elif tag == RAW:
            now[one] = took[two]
            wrote.add(one)
        elif tag == FIX:
            now[one] = two
        elif tag == MARK:
            stack.append((at, dict(now), set(wrote)))
        elif tag == EQ or tag == GE:
            if tag == EQ:
                good = now[one] == two
            else:
                good = now[one] >= two
            if not good:
                if not stack:
                    return "fin %d no" % d.num
                _mark, now, wrote = stack.pop()
                at += 1
                continue
        at += 1
    out = ["fin %d ok" % d.num]
    for k in sorted(wrote):
        store[k] = now[k]
        out.append("%d=%d" % (k, now[k]))
    return " ".join(out)
