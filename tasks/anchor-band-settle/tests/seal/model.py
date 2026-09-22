"""The sealed model: what every frame of a program must print.

Written apart from the reference solution and sharing no code with the agent's tree. It parses
the program itself, keeps its own box tree, and answers each frame from the contract in
tests/test_outputs.py. The reference replays the tree's change log with eager differences
pushed up each ancestor chain and keeps running-end arrays per row; this model applies the
edits itself, collects the boxes whose inputs changed, recomputes them bottom-up in order of
depth, and keeps a Fenwick tree over each row of children. Both have to be fast, because the
scale programs are generated at grading time and have to be answered here as well.

    expect(lines) -> the lines the program must print, one per frame

The generator in tests/gen.py also drives it one frame at a time through begin() and
one_frame(), with a trace list, so that it can shape each frame against the view as it really
stands. That is shaping only: a generated program is graded against expect() like any other.
"""

TMAX_FLOOR = 0


class Fen:
    """Prefix sums over one row of children, with point updates."""

    __slots__ = ("n", "t")

    def __init__(self, vals):
        n = len(vals)
        t = [0] * (n + 1)
        for i in range(1, n + 1):
            t[i] += vals[i - 1]
            j = i + (i & -i)
            if j <= n:
                t[j] += t[i]
        self.n = n
        self.t = t

    def add(self, i, d):
        i += 1
        t = self.t
        n = self.n
        while i <= n:
            t[i] += d
            i += i & -i

    def pre(self, i):
        """Sum of the first i entries."""
        s = 0
        t = self.t
        while i > 0:
            s += t[i]
            i -= i & -i
        return s

    def total(self):
        return self.pre(self.n)

    def first_past(self, x):
        """Smallest index whose running end exceeds x (n when none does)."""
        pos = 0
        rem = x
        t = self.t
        n = self.n
        step = 1 << n.bit_length()
        while step:
            nxt = pos + step
            if nxt <= n and t[nxt] <= rem:
                pos = nxt
                rem -= t[nxt]
            step >>= 1
        return pos


class Node:
    __slots__ = ("id", "own", "pin", "shut", "lift", "live", "kids", "up", "gone",
                 "depth", "i", "h", "c", "fen", "pins")

    def __init__(self, bid, own, fl, up, depth):
        self.id = bid
        self.own = own
        self.pin, self.shut, self.lift, self.live = fl
        self.kids = []
        self.up = up
        self.gone = False
        self.depth = depth
        self.i = 0
        self.h = 0
        self.c = 0
        self.fen = None
        self.pins = None


def parse_flags(toks):
    pin = None
    shut = lift = live = False
    for tok in toks:
        if tok.startswith("pin="):
            pin = int(tok[4:])
        elif tok == "shut":
            shut = True
        elif tok == "lift":
            lift = True
        elif tok == "live":
            live = True
        else:
            raise ValueError("unknown flag %r" % tok)
    return pin, shut, lift, live


class World:
    def __init__(self):
        self.vh = 0
        self.root = Node("", 0, (None, False, False, False), None, -1)
        self.by = {}
        self.tmax = TMAX_FLOOR
        self.memo = {}
        self.todo = {}
        self.rows = set()

    # ---- structure --------------------------------------------------------------------
    def attach(self, bid, pid, at, own, fl):
        up = self.root if pid == "-" else self.by[pid]
        b = Node(bid, own, fl, up, up.depth + 1)
        if at is None:
            up.kids.append(b)
        elif at > len(up.kids):
            raise ValueError("add %s: index %d past the end" % (bid, at))
        else:
            up.kids.insert(at, b)
        self.by[bid] = b
        if b.pin is not None and b.pin > self.tmax:
            self.tmax = b.pin
        self.rows.add(up)
        self.rows.add(b)
        self.mark(b)
        self.mark(up)
        return b

    def mark(self, b):
        self.todo.setdefault(b.depth, set()).add(b)

    def detach(self, b):
        up = b.up
        up.kids.remove(b)
        self.rows.add(up)
        self.mark(up)
        stack = [b]
        while stack:
            x = stack.pop()
            x.gone = True
            del self.by[x.id]
            stack.extend(x.kids)

    def refresh(self):
        """Recompute every changed box bottom-up, deepest first."""
        while self.todo:
            deep = max(self.todo)
            batch = self.todo.pop(deep)
            for b in batch:
                if b.gone:
                    continue
                if b in self.rows:
                    self.rows.discard(b)
                    for k, kid in enumerate(b.kids):
                        kid.i = k
                    b.fen = Fen([kid.c for kid in b.kids])
                    b.pins = [k for k, kid in enumerate(b.kids) if kid.pin is not None]
                if b is self.root:
                    continue
                h = b.own + (0 if b.shut else b.fen.total())
                c = 0 if b.lift else h
                b.h = h
                if c != b.c:
                    up = b.up
                    if up not in self.rows:
                        up.fen.add(b.i, c - b.c)
                    b.c = c
                    self.mark(up)
        self.memo = {}

    def span(self):
        return max(0, self.root.fen.total() - self.vh)

    def top(self, b):
        y = self.memo.get(b)
        if y is None:
            up = b.up
            if up is self.root:
                y = up.fen.pre(b.i)
            else:
                y = self.top(up) + up.own + up.fen.pre(b.i)
            self.memo[b] = y
        return y

    def start_of(self, b):
        if b is self.root:
            return 0
        return self.top(b) + b.own

    def end_of(self, b):
        """End of the section a pinned box sticks inside."""
        up = b.up
        if up is self.root:
            return self.root.fen.total()
        return self.top(up) + up.h

    def shows(self, b):
        """In the flow and not hidden."""
        if b.gone or b.lift:
            return False
        up = b.up
        while up is not self.root:
            if up.lift or up.shut:
                return False
            up = up.up
        return True

    def stuck(self, b, s):
        if b.pin is None or b.h <= 0:
            return None
        r = min(s + b.pin, self.end_of(b) - b.h)
        return r if r > self.top(b) else None

    def under_stuck(self, b, s):
        x = b
        while x is not self.root:
            if self.stuck(x, s) is not None:
                return True
            x = x.up
        return False

    def band(self, s):
        hi = s + self.tmax
        best = 0
        stack = [self.root]
        while stack:
            owner = stack.pop()
            base = self.start_of(owner)
            fen = owner.fen
            kids = owner.kids
            for k in owner.pins:
                kid = kids[k]
                y = base + fen.pre(k)
                if y >= hi:
                    break
                if kid.lift:
                    continue
                r = self.stuck(kid, s)
                if r is not None:
                    best = max(best, r + kid.h - s)
            k = fen.first_past(s - base)
            while k < len(kids):
                kid = kids[k]
                y = base + fen.pre(k)
                if y >= hi:
                    break
                if kid.c > 0 and not kid.shut:
                    stack.append(kid)
                k += 1
        return best

    def pick(self, s, band):
        u = s + band
        w = s + self.vh
        if u >= w:
            return None

        def look(owner):
            base = self.start_of(owner)
            fen = owner.fen
            kids = owner.kids
            k = fen.first_past(u - base)
            while k < len(kids):
                kid = kids[k]
                y = base + fen.pre(k)
                if y >= w:
                    return None
                k += 1
                if kid.c == 0 or kid.live or self.stuck(kid, s) is not None:
                    continue
                if y >= u and y + kid.h <= w:
                    return kid
                if not kid.shut:
                    inner = look(kid)
                    if inner is not None:
                        return inner
                return kid
            return None

        return look(self.root)


def live_above(b):
    while b is not None and b.id != "":
        if b.live:
            return True
        b = b.up
    return False


def begin(lines):
    """A world built from declaration lines (view, box, at), and the offset it starts at."""
    world = World()
    s = None
    for raw in lines:
        p = raw.split()
        if p[0] == "view":
            world.vh = int(p[1])
        elif p[0] == "box":
            world.attach(p[1], p[2], None, int(p[3]), parse_flags(p[4:]))
        elif p[0] == "at":
            s = int(p[1])
    world.rows.add(world.root)
    world.mark(world.root)
    world.refresh()
    return world, s


def expect(lines):
    world = World()
    frames = []
    s = None
    for raw in lines:
        p = raw.split()
        if not p:
            continue
        head = p[0]
        if head == "view":
            world.vh = int(p[1])
        elif head == "box":
            world.attach(p[1], p[2], None, int(p[3]), parse_flags(p[4:]))
        elif head == "at":
            s = int(p[1])
        elif head == "frame":
            frames.append([])
        else:
            frames[-1].append(p)
    world.rows.add(world.root)
    world.mark(world.root)
    world.refresh()

    out = []
    for n, edits in enumerate(frames, 1):
        s, word = one_frame(world, s, edits)
        out.append("%d %d %s" % (n, s, word))
    return out


def one_frame(world, s0, edits, trace=None):
    band0 = world.band(s0)
    held = world.pick(s0, band0)
    saved = []
    if held is not None:
        line = s0 + band0
        x = held
        while x is not world.root:
            saved.append((x, world.top(x) - line))
            x = x.up

    asked = None
    quiet = False
    for p in edits:
        head = p[0]
        if head == "to":
            asked = int(p[1])
            continue
        if head == "add":
            b = world.attach(p[1], p[2], int(p[3]), int(p[4]), parse_flags(p[5:]))
            quiet = quiet or live_above(b)
            continue
        b = world.by[p[1]]
        quiet = quiet or live_above(b)
        if head == "size":
            b.own = int(p[2])
            world.mark(b)
        elif head == "drop":
            world.detach(b)
        elif head in ("shut", "open"):
            b.shut = head == "shut"
            world.mark(b)
        elif head in ("lift", "sink"):
            b.lift = head == "lift"
            world.mark(b)
        elif head == "pin":
            b.pin = int(p[2])
            if b.pin > world.tmax:
                world.tmax = b.pin
            world.rows.add(b.up)
            world.mark(b.up)
        elif head == "unpin":
            b.pin = None
            world.rows.add(b.up)
            world.mark(b.up)
        else:
            raise ValueError("unknown edit %r" % head)
    world.refresh()

    last = world.span()

    def fit(x):
        return 0 if x < 0 else (last if x > last else x)

    if asked is not None:
        return fit(asked), "off scroll"
    if quiet:
        return fit(s0), "off live"
    if not saved:
        return fit(s0), "none"

    at = s0
    reached = []
    passes = 0
    while passes < 4:
        passes += 1
        band = world.band(at)
        holder = None
        for x, gap in saved:
            if world.shows(x) and x.h > 0 and not world.under_stuck(x, at):
                holder = (x, gap)
                break
        if holder is None:
            return fit(at), "none"
        x, gap = holder
        nxt = fit(world.top(x) - gap - band)
        if trace is not None:
            trace.append((at, band, x.id, nxt))
        if nxt == at:
            return at, x.id
        reached.append((nxt, passes, x))
        at = nxt
    low = min(reached, key=lambda r: (r[0], r[1]))
    return low[0], low[2].id
