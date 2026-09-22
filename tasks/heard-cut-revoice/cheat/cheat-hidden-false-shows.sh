#!/bin/bash
# hidden=false is taken to mean shown
set -euo pipefail

cat > /app/sr/look.py <<'PYEOF'
"""What the page says about a node, read off the page as it stands now.

A node is exposed when it is attached and no element at or above it hides it (`hidden` with any
value, or `aria-hidden="true"`; `aria-hidden="false"` never undoes an ancestor). Its region is
the nearest element at or above it carrying `aria-live` - `off` included, so an off region
nested in a polite one is a wall rather than a window. A region voices while it is exposed and
polite or assertive, and it lets through only the kinds its own `aria-relevant` names; an
`aria-relevant` anywhere else on the page means nothing.
"""

POL = ("polite", "assertive")
ALL = frozenset(("additions", "removals", "text"))
BASE = frozenset(("additions", "text"))


def hides(pg, e):
    return pg.attr(e, "hidden") not in (None, "false") or pg.attr(e, "aria-hidden") == "true"


def place(pg, n):
    """(exposed, region) for node n. The region is None when n is not exposed."""
    reg = None
    x = n
    while x is not None:
        if not pg.is_text(x):
            if hides(pg, x):
                return False, None
            if reg is None and pg.attr(x, "aria-live") is not None:
                reg = x
        if x == 0:
            return True, reg
        x = pg.up(x)
    return False, None


def region(pg, n):
    """The nearest element at or above n carrying aria-live, exposed or not."""
    x = n
    while x is not None:
        if not pg.is_text(x) and pg.attr(x, "aria-live") is not None:
            return x
        x = pg.up(x)
    return None


def voicing(pg, r):
    return pg.attr(r, "aria-live") in POL and place(pg, r)[0]


def loudness(pg, r):
    return pg.attr(r, "aria-live")


def relevant(pg, r):
    got = set()
    for tok in (pg.attr(r, "aria-relevant") or "").split():
        if tok == "all":
            return ALL
        if tok in ALL:
            got.add(tok)
    return frozenset(got) if got else BASE


def busy(pg, e):
    return pg.attr(e, "aria-busy") == "true"


def atomic(pg, e):
    v = pg.attr(e, "aria-atomic")
    return v if v in ("true", "false") else None
PYEOF

cat > /app/sr/know.py <<'PYEOF'
"""What the reader believes, and what the utterance it is playing will teach it.

Belief is kept per (region element, text node): the text the reader believes is there, and the
anchor - the parent the node had when that entry was written. Keying by region is what lets a
node that moved between two regions be a removal in one and an addition in the other, with
separate fates. The anchor is deliberately not refreshed by a move inside a region: a move there
is no difference, so nothing is spoken and nothing is learned, and a later removal is placed
where the listener last believed the node was.

The playing utterance's carried values sit on top of belief, never inside it. That is the whole
point of the layer: the listener learns them only when the utterance finishes, a cut throws them
away, and until one of those happens a difference is measured against what the reader *will*
believe - `expect`.
"""


class Know:
    def __init__(self):
        self.b = {}
        self.carry = {}
        self.at = {}

    def _note(self, k):
        r, n = k
        if k in self.b or k in self.carry:
            self.at.setdefault(n, set()).add(r)
        else:
            s = self.at.get(n)
            if s is not None:
                s.discard(r)
                if not s:
                    del self.at[n]

    def load(self, entries):
        for k, v in entries.items():
            self.b[k] = v
            self._note(k)

    def expect(self, k):
        got = self.carry.get(k)
        if got is not None:
            return got[0]
        return self.b.get(k)

    def believe(self, k, v):
        if v is None:
            self.b.pop(k, None)
        else:
            self.b[k] = v
        self._note(k)

    def absorb(self, k, v):
        """Believe the current value at once; the playing utterance stops carrying k."""
        self.carry.pop(k, None)
        self.believe(k, v)

    def take(self, carried):
        self.carry = carried
        for k in carried:
            self._note(k)

    def finish(self):
        done, self.carry = self.carry, {}
        for k, (v, _age) in done.items():
            self.believe(k, v)

    def cut(self):
        back, self.carry = self.carry, {}
        for k in back:
            self._note(k)
        return back

    def regions_of(self, n):
        return tuple(self.at.get(n, ()))
PYEOF

cat > /app/sr/watch.py <<'PYEOF'
"""Observation: which differences exist at the end of a tick, and what happens to each.

A difference is measured per (region, text node) between the current value - the node's text and
parent when it is exposed in that region - and what the reader will believe once the playing
utterance finishes, by presence and text only. A difference the reader cannot voice (its region
is off or not exposed) or that its region does not find relevant is absorbed on the spot; every
other one is in the waiting line, keeping the age of the tick that first observed it.

The model recomputes this for every key on every tick. That is correct and it is exactly what the
wide pages are there to rule out, so this only looks at keys something could have changed:

- a text record changes one node;
- adding, moving or dropping a node, or hiding or showing an element, changes the exposure,
  region or parent of every text node beneath it, changes whether every removal anchored beneath
  it is still placed there, and changes whether every region element beneath it is exposed;
- an aria-live or aria-relevant change on a region element reclassifies every difference in it;
- an aria-busy change can only hold or release differences in the region the element is in.

Nothing else on the page can change a key's value, whether it may be voiced, or what holds it.
"""
from . import look, unit


def differs(c, e):
    if (c is None) != (e is None):
        return True
    return c is not None and c[0] != e[0]


def kind(c, e):
    if e is None:
        return "additions"
    if c is None:
        return "removals"
    return "text"


class Watch:
    def __init__(self, pg, know, line):
        self.pg = pg
        self.know = know
        self.line = line

    def now(self, n):
        """(region, (text, parent)) for text node n exposed in a region, else (None, None)."""
        shown, r = look.place(self.pg, n)
        if not shown or r is None:
            return None, None
        return r, (self.pg.text(n), self.pg.up(n))

    def survey(self):
        out = {}
        pg = self.pg
        todo = [(0, None)]
        while todo:
            x, r = todo.pop()
            if pg.is_text(x):
                if r is not None:
                    out[(r, x)] = (pg.text(x), pg.up(x))
                continue
            if look.hides(pg, x):
                continue
            if pg.attr(x, "aria-live") is not None:
                r = x
            for y in pg.kids(x):
                todo.append((y, r))
        return out

    def settle(self, k, t, age=None, where=None):
        pg, know, line = self.pg, self.know, self.line
        r, n = k
        rr, cur = self.now(n) if where is None else where
        c = cur if rr == r else None
        e = know.expect(k)
        if not differs(c, e):
            line.drop(k)
            return
        if not look.voicing(pg, r) or kind(c, e) not in look.relevant(pg, r):
            know.absorb(k, c)
            line.drop(k)
            return
        if age is None:
            age = line.age.get(k, t)
        line.put(k, age, look.loudness(pg, r), unit.held(pg, know, k, c),
                 e[1] if c is None else None)

    def rehold(self, k):
        if k not in self.line.age:
            return
        r, n = k
        rr, cur = self.now(n)
        c = cur if rr == r else None
        self.line.hold(k, unit.held(self.pg, self.know, k, c))

    def _sweep(self, top, nodes, anchors, regs):
        pg = self.pg
        for x in pg.walk(top):
            if pg.is_text(x):
                nodes.add(x)
            else:
                anchors.add(x)
                if pg.attr(x, "aria-live") is not None:
                    regs.add(x)

    def scan(self, recs, t):
        pg = self.pg
        nodes, anchors, regs, busy = set(), set(), set(), set()
        for rec in recs:
            head = rec[0]
            if head == "text":
                nodes.add(rec[1])
            elif head in ("add", "move", "drop"):
                self._sweep(rec[1], nodes, anchors, regs)
            else:
                e, name = rec[1], rec[2]
                if name in ("hidden", "aria-hidden"):
                    self._sweep(e, nodes, anchors, regs)
                elif name in ("aria-live", "aria-relevant"):
                    if pg.attr(e, "aria-live") is not None:
                        regs.add(e)
                elif name == "aria-busy":
                    q = look.region(pg, e)
                    if q is not None:
                        busy.add(q)
        for n in nodes:
            where = self.now(n)
            ks = {(q, n) for q in self.know.regions_of(n)}
            ks.update((q, n) for q in self.line.regions_of(n))
            if where[0] is not None:
                ks.add((where[0], n))
            for k in ks:
                self.settle(k, t, where=where)
        for r in regs:
            for k in self.line.of_region(r):
                self.settle(k, t)
        for a in anchors:
            for k in self.line.anchored(a):
                self.rehold(k)
        for q in busy:
            for k in self.line.of_region(q):
                self.rehold(k)
PYEOF

cat > /app/sr/unit.py <<'PYEOF'
"""Where a difference sits: what holds it, and which unit it is spoken as.

Both questions start from one element. For an addition or a text change it is the node's parent
now. For a removal the node is nowhere now, so it is the anchor - the parent the node had when
the listener last believed it - provided that anchor is still exposed in the same region; if not,
the removal sits at its region element alone. The removal is placed where it was last believed,
not where anything is now, and moves inside a region never refresh that.

Holds read every element from the start up to and including the region element: one
`aria-busy="true"` among them holds the difference. Units walk the same path and stop at the
first element whose `aria-atomic` is `true` or `false`: `true` makes that element the unit,
`false` means the difference is spoken alone, and reaching the region element without either
means alone as well. A removal with no start element is always spoken alone.
"""
from . import look


def start(pg, know, k, cur):
    r, _n = k
    if cur is not None:
        return cur[1]
    a = know.expect(k)[1]
    shown, reg = look.place(pg, a)
    if shown and reg == r:
        return a
    return None


def held(pg, know, k, cur):
    r, _n = k
    s = start(pg, know, k, cur)
    x = r if s is None else s
    while True:
        if look.busy(pg, x):
            return True
        if x == r:
            return False
        x = pg.up(x)


def unit(pg, know, k, cur):
    r, _n = k
    s = start(pg, know, k, cur)
    if s is None:
        return None
    x = s
    while True:
        v = look.atomic(pg, x)
        if v == "true":
            return x
        if v == "false" or x == r:
            return None
        x = pg.up(x)


def read(pg, u):
    """The exposed text nodes and elements inside u, in document order."""
    texts, els = [], []
    todo = [u]
    while todo:
        x = todo.pop()
        if pg.is_text(x):
            texts.append(x)
            continue
        if look.hides(pg, x):
            continue
        els.append(x)
        todo.extend(reversed(pg.kids(x)))
    return texts, els
PYEOF

cat > /app/sr/line.py <<'PYEOF'
"""The waiting line: every difference the reader can voice, with its age.

A difference joins the line at the end of the tick that first observed it and keeps that age
while it persists, however often its text changes; a cut hands a carried difference back at the
age it had when the utterance took it. Held differences stay in the line but out of reach.

Selection is oldest first, assertive ahead of polite, ties to the lower text node id and then
the lower region id. Two heaps with lazy deletion give that in logarithmic time. An entry is
valid only while its key still has that age, is not held and still has that loudness; anything
else is thrown away when it surfaces. That is sound because a stale entry can only become valid
again through `put`, which pushes a fresh one anyway. Rescanning the line at every selection is
exactly as correct, and is what the held family is there to rule out.
"""
import heapq


class Line:
    def __init__(self):
        self.age = {}
        self.cls = {}
        self.held = set()
        self.heap = {"assertive": [], "polite": []}
        self.reg = {}
        self.anc = {}
        self.anchor = {}
        self.nod = {}

    def put(self, k, age, cls, held, anchor):
        r, n = k
        was = self.anchor.get(k)
        if was is not None and was != anchor:
            self._unanchor(k, was)
        self.age[k] = age
        self.cls[k] = cls
        self.reg.setdefault(r, set()).add(k)
        self.nod.setdefault(n, set()).add(r)
        if anchor is not None:
            self.anchor[k] = anchor
            self.anc.setdefault(anchor, set()).add(k)
        else:
            self.anchor.pop(k, None)
        if held:
            self.held.add(k)
        else:
            self.held.discard(k)
            heapq.heappush(self.heap[cls], (age, n, r))

    def hold(self, k, held):
        if k not in self.age:
            return
        if held:
            self.held.add(k)
        elif k in self.held:
            self.held.discard(k)
            r, n = k
            heapq.heappush(self.heap[self.cls[k]], (self.age[k], n, r))

    def _unanchor(self, k, a):
        s = self.anc.get(a)
        if s is not None:
            s.discard(k)
            if not s:
                del self.anc[a]

    def drop(self, k):
        if k not in self.age:
            return
        r, n = k
        del self.age[k]
        del self.cls[k]
        self.held.discard(k)
        s = self.reg.get(r)
        if s is not None:
            s.discard(k)
            if not s:
                del self.reg[r]
        s = self.nod.get(n)
        if s is not None:
            s.discard(r)
            if not s:
                del self.nod[n]
        a = self.anchor.pop(k, None)
        if a is not None:
            self._unanchor(k, a)

    def regions_of(self, n):
        return tuple(self.nod.get(n, ()))

    def of_region(self, r):
        return list(self.reg.get(r, ()))

    def anchored(self, a):
        return list(self.anc.get(a, ()))

    def ready(self, k):
        return k in self.age and k not in self.held

    def top(self, cls):
        pile = self.heap[cls]
        while pile:
            age, n, r = pile[0]
            k = (r, n)
            if self.age.get(k) == age and k not in self.held and self.cls.get(k) == cls:
                return k
            heapq.heappop(pile)
        return None
PYEOF

cat > /app/sr/voice.py <<'PYEOF'
"""The reader: one tick at a time, in the order the model fixes.

At the end of every tick, after the tick's mutations: the playing utterance finishes if its time
is up, and teaches its carried values; the page is observed and every difference absorbed, aged
or held; a pending assertive difference cuts a playing polite utterance, and everything the cut
utterance carried goes back into the line at the age it had when it was taken; and whenever the
reader is free it takes the oldest pending difference, assertive before polite.

What it says is decided when it starts, never earlier. A difference inside an atomic unit makes
the whole unit speak - its exposed text as it stands now - and the utterance carries every pending
difference whose unit that is, however young, while held ones stay behind even though their text
is being read. An utterance of w words started at the end of tick t finishes at the end of tick
t + w. A unit with no exposed text says nothing: its differences are believed at once and the
reader chooses again in the same tick.
"""
from . import look, say, unit
from .know import Know
from .line import Line
from .watch import Watch


class Reader:
    def __init__(self, pg):
        self.pg = pg
        self.know = Know()
        self.line = Line()
        self.watch = Watch(pg, self.know, self.line)
        self.play = None

    def load(self):
        self.know.load(self.watch.survey())

    def _pick(self):
        return self.line.top("assertive") or self.line.top("polite")

    def _group(self, u):
        pg, know, line, watch = self.pg, self.know, self.line, self.watch
        texts, els = unit.read(pg, u)
        group = []
        for x in texts:
            r, cur = watch.now(x)
            k = (r, x)
            if line.ready(k) and unit.unit(pg, know, k, cur) == u:
                group.append((k, cur))
        for a in els:
            for k in line.anchored(a):
                if line.ready(k) and unit.unit(pg, know, k, None) == u:
                    group.append((k, None))
        return " ".join(pg.text(x) for x in texts), group

    def step(self, t, recs):
        pg, know, line, watch = self.pg, self.know, self.line, self.watch
        out = []
        if self.play is not None and self.play[1] == t:
            know.finish()
            self.play = None

        watch.scan(recs, t)

        if self.play is not None and self.play[0] == "polite" and line.top("assertive"):
            out.append(say.cut(t))
            self.play = None
            for k, (_v, age) in know.cut().items():
                watch.settle(k, t, age=age)

        while self.play is None:
            k0 = self._pick()
            if k0 is None:
                break
            r0, n0 = k0
            rr, cur = watch.now(n0)
            c0 = cur if rr == r0 else None
            u = unit.unit(pg, know, k0, c0)
            if u is not None:
                words, group = self._group(u)
            else:
                group = [(k0, c0)]
                words = c0[0] if c0 is not None else "removed " + know.expect(k0)[0]
            carried = {k: (c, line.age[k]) for k, c in group}
            for k in carried:
                line.drop(k)
            if not words:
                for k, (v, _age) in carried.items():
                    know.believe(k, v)
                continue
            cls = look.loudness(pg, r0)
            know.take(carried)
            self.play = (cls, t + len(words.split(" ")))
            out.append(say.start(t, cls, words))
        return out
PYEOF

