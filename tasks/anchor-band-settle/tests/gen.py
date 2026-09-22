"""Programs generated from a seed drawn after the agent's container is gone.

The families are shaped around the decisions instead of sampled from the input space. An
unshaped population almost never makes an adjustment stick a header, almost never cycles and
almost never hands the view to a container halfway through a frame (measured on 41,656 fuzzed
frames: 0.5% changed holder mid-loop, 0.5% ran out of passes), so every wrong reading of those
rules would score the same as the right one. Each family below concentrates one mechanism, and
the two scale families exist for the execution limit rather than for a rule.

  plain    content above the view resolves, rows below open and close: ordinary holding
  band     the view sits inside sections whose headers are stuck, and content above changes
  stick    an edit between a header and the holder moves the holder across the stick line
  cycle    the move lands inside the band a header would add, so passes alternate
  push     the view near a section's end, where the end pushes a stuck header off
  fall     the holder is dropped, hidden, lifted, emptied or pinned, and a container takes over
  turn     the adjustment itself sticks a header over the holder, which is lost halfway
  clamp    short documents and deep cuts, so passes run into the ends of the scroll range
  switch   explicit scrolls and edits inside live boxes
  top      the view at offset zero with content arriving above the holder
  edge     zero heights, exact boundaries, tall boxes, headers wider than the view
  mix      every statement, long stateful runs, no resets
  rare     the old offset past the new range, later passes with nothing left, empty boxes
  long     scale: forty thousand boxes, a hundred chapters of twenty headed sections
  wide     scale: forty thousand boxes, a hundred and fifty broad sections, shallow

Shaping drives the sealed model one frame at a time (model.begin, model.one_frame) so that each
frame is aimed at the view as it really stands. That is shaping only: every program is graded
against model.expect like any other, and a family can only make a wrong reading more likely to
be caught, never change what correct is.

    python3 gen.py --seed <hex> --per <n> --out <file>
"""
import copy
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "seal"))

import model  # noqa: E402

FAMILIES = (
    ("plain", False),
    ("band", False),
    ("stick", False),
    ("cycle", False),
    ("push", False),
    ("fall", False),
    ("turn", False),
    ("clamp", False),
    ("switch", False),
    ("top", False),
    ("edge", False),
    ("mix", False),
    ("rare", False),
    ("long", True),
    ("wide", True),
)

BIG = 3
BIG_FRAMES = 10000


# ---------------------------------------------------------------------------------------
# A program being written, with the model as its live shadow.

class Pen:
    def __init__(self, rng, vh):
        self.rng = rng
        self.vh = vh
        self.lines = ["view %d" % vh]
        self.n = 0
        self.world = None
        self.s = None

    def fresh(self, tag):
        self.n += 1
        return "%s%d" % (tag, self.n)

    def box(self, par, own, pin=None, flags=()):
        bid = self.fresh("b" if pin is None else "h")
        fl = (["pin=%d" % pin] if pin is not None else []) + list(flags)
        self.lines.append(" ".join(["box", bid, par, str(own)] + fl))
        return bid

    def start(self, where=None):
        """Close the declarations with `at`, at a chosen offset or a random one."""
        world, _ = model.begin(self.lines + ["at 0"])
        span = world.span()
        s = self.rng.randint(0, span) if where is None else max(0, min(where(world), span))
        self.lines.append("at %d" % s)
        self.world, self.s = model.begin(self.lines)

    def valid(self, edits):
        """The edits in order, less any that name a box an earlier one already dropped, and
        less any add whose index is past the end of its row as the frame has left it."""
        gone, keep = set(), []
        rows = {}
        born = {}

        def length(pid):
            if pid not in rows:
                owner = self.world.root if pid == "-" else self.world.by.get(pid)
                rows[pid] = len(owner.kids) if owner is not None else 0
            return rows[pid]

        def parent_of(bid):
            if bid in born:
                return born[bid]
            x = self.world.by.get(bid)
            return "-" if x is None or x.up is self.world.root else x.up.id

        for e in edits:
            if not e:
                continue
            parts = e.split()
            head = parts[0]
            if head == "to":
                keep.append(e)
                continue
            named = parts[2] if head == "add" else parts[1]
            if named in gone or (named != "-" and named not in self.world.by
                                 and named not in born):
                continue
            if head == "add":
                if int(parts[3]) > length(named):
                    continue
                rows[named] = length(named) + 1
                born[parts[1]] = named
                rows[parts[1]] = 0
            if head == "drop":
                pid = parent_of(named)
                rows[pid] = length(pid) - 1
                stack = [self.world.by.get(named)]
                gone.add(named)
                while stack:
                    x = stack.pop()
                    if x is None:
                        continue
                    gone.add(x.id)
                    stack.extend(x.kids)
                for k in keep:
                    kp = k.split()
                    if kp[0] == "add" and kp[2] in gone:
                        gone.add(kp[1])
            keep.append(e)
        return keep

    def frame(self, edits):
        edits = self.valid(edits)
        self.lines.append("frame")
        self.lines.extend(edits)
        trace = []
        self.s, word = model.one_frame(self.world, self.s, [e.split() for e in edits], trace)
        return word, trace

    def trial(self, edits, keep=None):
        """What a frame would print, without writing it. With `keep`, the world it leaves is
        appended to that list, so a caller can ask about the tree after the frame."""
        edits = self.valid(edits)
        world = copy.deepcopy(self.world)
        trace = []
        s, word = model.one_frame(world, self.s, [e.split() for e in edits], trace)
        if keep is not None:
            keep.append(world)
        return s, word, trace

    # ---- the view as it stands --------------------------------------------------------
    def node(self, bid):
        return self.world.by.get(bid)

    def laid(self):
        """Every laid-out box, in document order, with its top and height."""
        out = []
        w = self.world

        def walk(b):
            for k in b.kids:
                if k.lift:
                    continue
                out.append((k, w.top(k), k.h))
                if not k.shut:
                    walk(k)

        walk(w.root)
        return out

    def band(self):
        return self.world.band(self.s)

    def holder(self):
        return self.world.pick(self.s, self.band())

    def chain(self):
        x = self.holder()
        out = []
        while x is not None and x is not self.world.root:
            out.append(x)
            x = x.up
        return out

    def above(self):
        return [b for b, y, h in self.laid() if y + h <= self.s and h > 0]

    def inside(self):
        s, w = self.s, self.s + self.vh
        return [b for b, y, h in self.laid() if y < w and y + h > s]

    def below(self):
        return [b for b, y, h in self.laid() if y >= self.s + self.vh]

    def pinned(self):
        return [b for b, y, h in self.laid() if b.pin is not None]

    def all_ids(self):
        return list(self.world.by)


# ---------------------------------------------------------------------------------------
# Documents.

def row(p, par, rng, zero=0.04):
    r = rng.random()
    if r < zero:
        own = 0
    elif r < 0.5:
        own = rng.randint(10, 40)
    elif r < 0.85:
        own = rng.randint(30, 90)
    else:
        own = rng.randint(80, 200)
    b = p.box(par, own)
    if rng.random() < 0.18:
        for _ in range(rng.randint(1, 3)):
            p.box(b, rng.randint(8, 30))
    return b


def document(p, rng, sections=(3, 6), rows=(3, 8), head=0.7, sub=0.35, zero=0.04,
             shut=0.0, lift=0.0, live=0.0):
    """Sections of rows, some with nested parts, most with a header that sticks."""
    for _ in range(rng.randint(*sections)):
        sec = p.box("-", rng.choice([0, 8, 12, 20]))
        hh = None
        if rng.random() < head:
            hh = rng.choice([16, 20, 24, 30])
            p.box(sec, hh, pin=rng.choice([0, 0, 0, 4, 10]))
        for _ in range(rng.randint(*rows)):
            if rng.random() < sub:
                part = p.box(sec, rng.choice([0, 6, 10]))
                if rng.random() < head:
                    inset = hh if hh is not None and rng.random() < 0.7 else rng.choice([0, 12, 20, 30])
                    p.box(part, rng.choice([14, 18, 22]), pin=inset)
                for _ in range(rng.randint(2, 5)):
                    row(p, part, rng, zero)
            else:
                row(p, sec, rng, zero)
        if rng.random() < shut:
            p.box(sec, rng.randint(10, 40), flags=("shut",))
        if rng.random() < lift:
            p.box(sec, rng.randint(10, 60), flags=("lift",))
        if rng.random() < live:
            lv = p.box(sec, rng.randint(10, 60), flags=("live",))
            if rng.random() < 0.5:
                p.box(lv, rng.randint(10, 40))


# ---------------------------------------------------------------------------------------
# Edits, aimed at the view as it stands.

def grow_or_shrink(rng, b):
    return "size %s %d" % (b.id, max(0, b.own + rng.choice([-1, 1]) * rng.randint(5, 90)))


def ordinary(p, rng, keep=()):
    """One everyday edit: content above resolves, rows below change, nothing near the holder."""
    keep = set(keep)
    k = rng.random()
    above = [b for b in p.above() if b not in keep]
    below = [b for b in p.below() if b not in keep]
    pool = above if (k < 0.55 and above) else (below or above)
    if not pool:
        return None
    b = rng.choice(pool)
    j = rng.random()
    if j < 0.6:
        return grow_or_shrink(rng, b)
    if j < 0.75:
        par = b.up.id if b.up is not p.world.root else "-"
        at = rng.randint(0, len(b.up.kids))
        return "add %s %s %d %d" % (p.fresh("b"), par, at, rng.randint(10, 80))
    if j < 0.85 and not b.kids:
        return "drop %s" % b.id
    if b.kids:
        return "%s %s" % ("open" if b.shut else "shut", b.id)
    return grow_or_shrink(rng, b)


def reset(p, rng):
    """An explicit scroll to somewhere with a header near the top of the view."""
    pins = p.pinned()
    if pins and rng.random() < 0.8:
        h = rng.choice(pins)
        y = p.world.top(h) + rng.randint(-40, 60)
    else:
        y = rng.randint(0, max(0, p.world.span()))
    p.frame(["to %d" % max(0, y)])


def passes(trace):
    """How a trial frame settled: number of passes, and whether the last one stood still."""
    if not trace:
        return 0, True
    at, _band, _x, nxt = trace[-1]
    return len(trace), at == nxt


def headers_near(p, reach=160):
    return [h for h in p.pinned() if abs(p.world.top(h) - p.s) < reach]


def candidates(p, rng):
    """Edit lists that can change the stuck set during the adjustment.

    A holder keeps its distance below the band, so the stuck set only moves when a header
    moves relative to the holder, when a header's own inset or pin changes, when a section's
    end moves under a stuck header, when the holder is lost and a container jumps the view, or
    when a pass is clamped. Growing or shrinking content between a stuck header and the holder
    cannot do it: that content is already above the line the holder is measured from.
    """
    w = p.world
    out = []
    hold = p.holder()
    chain = p.chain()
    heads = headers_near(p)
    laid = p.laid()
    if hold is not None:
        y0 = w.top(hold)
        # content between the holder and a header below it
        for h in heads:
            yh = w.top(h)
            if yh > y0:
                mids = [b for b, y, hh in laid if y0 < y < yh and b not in chain and b.kids == []]
                if mids:
                    b = rng.choice(mids)
                    out.append(["size %s %d" % (b.id, max(0, b.own + rng.randint(-60, 60)))])
    for h in heads:
        out.append(["pin %s %d" % (h.id, max(0, h.pin + rng.randint(-30, 30)))])
        out.append(["size %s %d" % (h.id, max(1, h.own + rng.randint(-15, 25)))])
        if rng.random() < 0.3:
            out.append(["unpin %s" % h.id])
        sec = h.up
        if sec is not w.root:
            tail = [k for k in sec.kids[sec.kids.index(h) + 1:] if k not in chain]
            if tail:
                b = rng.choice(tail)
                out.append(["size %s %d" % (b.id, max(0, b.own + rng.randint(-80, 40)))])
    near = [b for b, y, hh in laid if abs(y - p.s) < 120 and b.pin is None and b not in chain]
    if near:
        b = rng.choice(near)
        out.append(["pin %s %d" % (b.id, rng.randint(0, 50))])
    d = disqualify(p, rng)
    if d:
        out.append([d])
    o = ordinary(p, rng, chain)
    if o:
        out.append([o])
    rng.shuffle(out)
    return out


def search(p, rng, want, tries=14):
    """The first candidate whose trial frame satisfies want(trace); else any candidate."""
    fallback = None
    for cand in candidates(p, rng)[:tries]:
        _s, _word, trace = p.trial(cand)
        if want(trace):
            return cand
        fallback = fallback or cand
    return fallback or []


def band_moves(trace):
    """The band read by some pass differs from the one before it."""
    return any(a[1] != b[1] for a, b in zip(trace, trace[1:]))


# ---------------------------------------------------------------------------------------
# The families.

def fam_plain(rng):
    p = Pen(rng, rng.randint(120, 260))
    document(p, rng, head=0.15, sub=0.3)
    p.start()
    for _ in range(rng.randint(10, 24)):
        edits = [e for e in (ordinary(p, rng, p.chain()) for _ in range(rng.randint(0, 3))) if e]
        p.frame(edits)
    return p.lines


def fam_band(rng):
    p = Pen(rng, rng.randint(120, 260))
    document(p, rng, head=0.95, sub=0.45)
    p.start()
    for f in range(rng.randint(10, 22)):
        if f % 5 == 0:
            reset(p, rng)
            continue
        edits = [e for e in (ordinary(p, rng, p.chain()) for _ in range(rng.randint(1, 3))) if e]
        p.frame(edits)
    return p.lines


def fam_stick(rng):
    """The adjustment moves the band once and settles on the pass after."""
    p = Pen(rng, rng.randint(120, 240))
    document(p, rng, head=0.95, sub=0.5)
    p.start()
    for f in range(rng.randint(10, 20)):
        if f % 4 == 0:
            reset(p, rng)
            continue
        p.frame(search(p, rng, lambda tr: band_moves(tr) and passes(tr)[1]))
    return p.lines


def fam_cycle(rng):
    """The passes never agree, or agree only on the last one allowed."""
    p = Pen(rng, rng.randint(120, 240))
    document(p, rng, head=0.95, sub=0.5)
    p.start()
    for f in range(rng.randint(10, 20)):
        if f % 4 == 0:
            reset(p, rng)
            continue
        if rng.random() < 0.25:
            p.frame(search(p, rng, lambda tr: passes(tr) == (4, True), tries=20))
        else:
            p.frame(search(p, rng, lambda tr: passes(tr) == (4, False), tries=20))
    return p.lines


def fam_push(rng):
    p = Pen(rng, rng.randint(120, 240))
    document(p, rng, sections=(4, 8), rows=(2, 5), head=0.95, sub=0.5)

    def near_end(world):
        heads = [b for b in world.by.values() if b.pin is not None and world.shows(b)]
        if not heads:
            return 0
        h = rng.choice(heads)
        return world.end_of(h) - h.h - h.pin + rng.randint(-20, 20)

    p.start(near_end)
    for f in range(rng.randint(10, 20)):
        if f % 4 == 0:
            heads = [b for b in p.pinned()]
            if heads:
                h = rng.choice(heads)
                p.frame(["to %d" % max(0, p.world.end_of(h) - h.h - h.pin + rng.randint(-25, 25))])
                continue
        hold = p.holder()
        edits = []
        heads = [h for h in p.pinned() if p.world.stuck(h, p.s) is not None]
        if heads:
            h = rng.choice(heads)
            sec = h.up if h.up is not p.world.root else None
            if sec is not None:
                rows = [k for k in sec.kids if k is not h and k is not hold]
                if rows:
                    r = rng.choice(rows)
                    edits.append("size %s %d" % (r.id, max(0, r.own + rng.randint(-50, 50))))
        o = ordinary(p, rng, p.chain())
        if o and rng.random() < 0.5:
            edits.append(o)
        p.frame(edits)
    return p.lines


def disqualify(p, rng):
    """An edit that takes the holder, or a box above it, out of the running."""
    chain = p.chain()
    if not chain:
        return None
    x = chain[0] if rng.random() < 0.6 or len(chain) == 1 else rng.choice(chain[1:])
    k = rng.random()
    if k < 0.3:
        return "drop %s" % x.id
    if k < 0.45 and x.up is not p.world.root:
        return "shut %s" % x.up.id
    if k < 0.6:
        return "lift %s" % x.id
    if k < 0.75 and not x.kids:
        return "size %s 0" % x.id
    if k < 0.85:
        y = p.world.top(x)
        return "pin %s %d" % (x.id, max(0, y - p.s + rng.randint(1, 30)))
    if k < 0.93:
        return "pin %s %d" % (chain[-1].id, rng.randint(0, 30))
    return "drop %s" % chain[-1].id if len(chain) > 1 else "drop %s" % x.id


def fam_fall(rng):
    p = Pen(rng, rng.randint(120, 260))
    document(p, rng, head=0.7, sub=0.55)
    p.start()
    for f in range(rng.randint(10, 22)):
        if not p.world.by:
            break
        if f % 4 == 3:
            reset(p, rng)
            continue
        edits = []
        d = disqualify(p, rng)
        if d:
            edits.append(d)
        for _ in range(rng.randint(0, 2)):
            o = ordinary(p, rng, p.chain())
            if o and not o.startswith("drop"):
                edits.append(o)
        p.frame(edits)
    return p.lines


def fam_turn(rng):
    """Frames whose own adjustment disqualifies the holder halfway, found by trial."""
    p = Pen(rng, rng.randint(120, 240))
    document(p, rng, head=0.98, sub=0.7)
    p.start()
    for f in range(rng.randint(10, 20)):
        if f % 3 == 0:
            reset(p, rng)
            continue
        p.frame(search(p, rng, lambda tr: len({t[2] for t in tr}) > 1, tries=20))
    return p.lines


def fam_clamp(rng):
    p = Pen(rng, rng.randint(120, 260))
    document(p, rng, sections=(2, 4), rows=(2, 5), head=0.95, sub=0.4)
    p.start(lambda w: w.span() - rng.randint(0, 30))
    for f in range(rng.randint(10, 20)):
        edits = []
        k = rng.random()

        below = p.below()
        inside = [b for b in p.inside() if b not in p.chain()]
        if k < 0.35 and (below or inside):
            b = rng.choice(below or inside)
            edits.append("size %s %d" % (b.id, max(0, b.own - rng.randint(20, 150))))
        elif k < 0.55 and below:
            edits.append("drop %s" % rng.choice(below).id)
        elif k < 0.7:
            edits.append(ordinary(p, rng, p.chain()) or "to %d" % p.world.span())
        elif k < 0.85:
            edits.append("to %d" % (p.world.span() + rng.randint(0, 80)))
        else:
            a = p.above()
            if a:
                b = rng.choice(a)
                edits.append("size %s %d" % (b.id, b.own + rng.randint(10, 120)))
        if rng.random() < 0.3:
            o = ordinary(p, rng, p.chain())
            if o:
                edits.append(o)
        p.frame([e for e in edits if e])
    return p.lines


def fam_switch(rng):
    p = Pen(rng, rng.randint(120, 260))
    document(p, rng, head=0.6, sub=0.35, live=0.7)
    p.start()
    for f in range(rng.randint(10, 22)):
        edits = []
        k = rng.random()
        lives = [b for b in p.world.by.values() if model.live_above(b)]
        tops = [b for b in lives if b.live and p.world.shows(b)]
        if tops and rng.random() < 0.2:
            b = rng.choice(tops)
            p.frame(["to %d" % max(0, p.world.top(b) + rng.randint(-10, 10))])
            continue
        if k < 0.3:
            edits.append("to %d" % rng.randint(0, p.world.span() + 120))
            if rng.random() < 0.35:
                edits.append("to %d" % rng.randint(0, p.world.span() + 120))
            if rng.random() < 0.5:
                o = ordinary(p, rng)
                if o:
                    edits.insert(rng.randint(0, len(edits)), o)
        elif k < 0.7 and lives:
            b = rng.choice(lives)
            j = rng.random()
            if j < 0.5:
                edits.append(grow_or_shrink(rng, b))
            elif j < 0.7:
                edits.append("add %s %s %d %d" % (p.fresh("b"), b.id, len(b.kids), rng.randint(10, 60)))
            elif j < 0.85 and b.kids:
                edits.append("drop %s" % rng.choice(b.kids).id)
            else:
                edits.append("%s %s" % ("open" if b.shut else "shut", b.id))
            if rng.random() < 0.5:
                o = ordinary(p, rng, p.chain())
                if o:
                    edits.append(o)
            if rng.random() < 0.15:
                edits.append("to %d" % rng.randint(0, p.world.span()))
        elif k < 0.8:
            a = p.above() or p.all_ids()
            if a:
                par = rng.choice([x for x in p.above() if x.up is p.world.root] or [p.world.root])
                pid = "-" if par is p.world.root else par.id
                at = rng.randint(0, len(par.kids))
                edits.append("add %s %s %d %d live" % (p.fresh("b"), pid, at, rng.randint(10, 60)))
        else:
            o = ordinary(p, rng, p.chain())
            if o:
                edits.append(o)
        p.frame(edits)
    return p.lines


def fam_top(rng):
    p = Pen(rng, rng.randint(120, 260))
    document(p, rng, head=0.5, sub=0.3)
    p.start(lambda w: 0)
    for f in range(rng.randint(8, 18)):
        edits = []
        hold = p.holder()
        k = rng.random()
        if k < 0.35:
            edits.append("add %s - 0 %d" % (p.fresh("b"), rng.randint(10, 90)))
        elif k < 0.6 and hold is not None:
            x = hold
            while x.up is not p.world.root:
                x = x.up
            if x is not hold:
                edits.append("size %s %d" % (x.id, x.own + rng.randint(5, 60)))
            else:
                edits.append("add %s - 0 %d" % (p.fresh("b"), rng.randint(10, 90)))
        elif k < 0.75:
            edits.append("to 0")
        else:
            o = ordinary(p, rng, p.chain())
            if o:
                edits.append(o)
        if p.s != 0 and rng.random() < 0.5:
            edits.append("to 0")
        p.frame(edits)
    return p.lines


def fam_edge(rng):
    p = Pen(rng, rng.randint(80, 200))
    document(p, rng, head=0.8, sub=0.4, zero=0.3, shut=0.3, lift=0.3)
    # A header taller than the view, somewhere, so the part below the band can be empty.
    if rng.random() < 0.5:
        sec = p.box("-", 10)
        p.box(sec, p.vh + rng.randint(0, 40), pin=0)
        for _ in range(rng.randint(2, 4)):
            p.box(sec, rng.randint(20, 80))
    # A pinned box of no height, and one inside a shut row.
    sec = p.box("-", 0)
    p.box(sec, 0, pin=rng.randint(0, 20))
    shut = p.box(sec, 12, flags=("shut",))
    p.box(shut, 20, pin=0)
    for _ in range(rng.randint(2, 4)):
        p.box(sec, rng.randint(0, 60))
    p.start()
    for f in range(rng.randint(10, 20)):
        edits = []
        k = rng.random()
        laid = p.laid()
        u = p.s + p.band()
        if k < 0.3 and laid:
            b, y, h = rng.choice(laid)
            edits.append("to %d" % max(0, y + h - p.band()))
        elif k < 0.5 and laid:
            b, y, h = rng.choice(laid)
            edits.append("to %d" % max(0, y - p.band()))
        elif k < 0.65:
            hs = p.pinned()
            if hs:
                h = rng.choice(hs)
                edits.append("to %d" % max(0, p.world.top(h) - h.pin))
        elif k < 0.72 and laid:
            b, y, h = rng.choice(laid)
            edits.append("size %s %d" % (b.id, rng.choice([0, 0, b.own + 1, max(0, b.own - 1)])))
        elif k < 0.8:
            empties = [b for b, y, h in laid if h == 0]
            if empties:
                b = rng.choice(empties)
                edits.append("to %d" % max(0, p.world.top(b) - p.band() - rng.randint(1, 20)))
                if b.pin is None and rng.random() < 0.5:
                    edits = ["pin %s %d" % (b.id, rng.randint(5, 30))]
        else:
            o = ordinary(p, rng, p.chain())
            if o:
                edits.append(o)
        del u
        p.frame(edits)
    return p.lines


def fam_mix(rng):
    p = Pen(rng, rng.randint(100, 260))
    document(p, rng, sections=(3, 7), head=0.7, sub=0.45, zero=0.06, shut=0.2, lift=0.2, live=0.2)
    p.start()
    makers = [
        lambda: ordinary(p, rng, p.chain()),
        lambda: (candidates(p, rng) or [None])[0],
        lambda: disqualify(p, rng),
        lambda: "to %d" % rng.randint(0, p.world.span() + 50),
        lambda: ordinary(p, rng),
    ]
    weights = [5, 3, 2, 1, 2]
    for _ in range(rng.randint(24, 44)):
        if not p.world.by:
            break
        edits = []
        for _ in range(rng.choice([0, 1, 1, 2, 2, 3])):
            e = rng.choices(makers, weights)[0]()
            if isinstance(e, list):
                edits.extend(e)
            elif e:
                edits.append(e)
        # Two edits naming one dropped box would be invalid; keep the first.
        seen, keep = set(), []
        for e in edits:
            parts = e.split()
            if parts[0] != "to" and parts[0] != "add" and parts[1] in seen:
                continue
            if parts[0] == "drop":
                x = p.node(parts[1])
                stack = [x] if x else []
                while stack:
                    y = stack.pop()
                    seen.add(y.id)
                    stack.extend(y.kids)
            keep.append(e)
        p.frame(keep)
    return p.lines


# ---------------------------------------------------------------------------------------
# The scale families. Written blind rather than shaped through the model, because a shadow
# of forty thousand boxes would make generation cost more than grading.

class Sh:
    def __init__(self):
        self.n = 0
        self.par = {}
        self.kids = {"-": []}
        self.own = {}
        self.pin = {}
        self.lift = set()
        self.shut = set()

    def new(self, tag, par, own, at=None, pin=None):
        self.n += 1
        bid = "%s%d" % (tag, self.n)
        self.par[bid] = par
        self.kids[bid] = []
        row_ = self.kids[par]
        row_.insert(len(row_) if at is None else at, bid)
        self.own[bid] = own
        if pin is not None:
            self.pin[bid] = pin
        return bid

    def drop(self, bid):
        self.kids[self.par[bid]].remove(bid)
        todo = [bid]
        while todo:
            x = todo.pop()
            todo.extend(self.kids.pop(x))
            del self.par[x]
            del self.own[x]
            self.pin.pop(x, None)
            self.lift.discard(x)
            self.shut.discard(x)

    def tops(self):
        out = {}

        def walk(b, y):
            if b in self.lift:
                return 0
            out[b] = y
            h = self.own[b]
            if b not in self.shut:
                for c in self.kids[b]:
                    h += walk(c, y + h)
            return h

        y = 0
        for b in self.kids["-"]:
            y += walk(b, y)
        return out, y


def build_long(rng):
    sh, order = Sh(), []
    for _c in range(100):
        c = sh.new("c", "-", 30)
        order.append(c)
        order.append(sh.new("h", c, 36, pin=0))
        for _s in range(20):
            s = sh.new("s", c, 12)
            order.append(s)
            order.append(sh.new("h", s, 28, pin=36))
            for _r in range(12):
                r = sh.new("r", s, rng.choice([20, 24, 40, 60, 90, 140]))
                order.append(r)
                if rng.random() < 0.25:
                    for _k in range(rng.randint(1, 3)):
                        order.append(sh.new("r", r, rng.choice([16, 20, 30])))
    return sh, order, 800


def build_wide(rng):
    sh, order = Sh(), []
    for _s in range(150):
        s = sh.new("s", "-", 20)
        order.append(s)
        order.append(sh.new("h", s, 32, pin=0))
        for i in range(240):
            if i % 60 == 30:
                part = sh.new("p", s, 14)
                order.append(part)
                order.append(sh.new("h", part, 24, pin=32))
                for _k in range(rng.randint(2, 5)):
                    order.append(sh.new("r", part, rng.choice([18, 22, 36])))
            else:
                order.append(sh.new("r", s, rng.choice([18, 22, 36, 54, 80])))
    return sh, order, 600


def big_frames(rng, sh, vh, count, lines):
    """Edits clustered around a wandering view, with an explicit scroll every two hundred."""
    rows = [b for b in sh.par if b[0] == "r"]
    focus = None
    for f in range(count):
        lines.append("frame")
        if focus is None or f % 200 == 0:
            tops, end = sh.tops()
            pool = [b for b in rows if b in sh.par and b in tops]
            focus = rng.choice(pool)
            lines.append("to %d" % max(0, min(tops[focus] - rng.randint(0, vh // 2), end - vh)))
            continue
        par = sh.par.get(focus)
        near = sh.kids[par] if par is not None else sh.kids["-"]
        for _e in range(rng.randint(1, 3)):
            pool = [b for b in near if b in sh.par and b[0] != "h"]
            k = rng.random()
            if not pool or k < 0.1:
                at_par = par if par in sh.kids else "-"
                at = rng.randint(0, len(sh.kids[at_par]))
                bid = sh.new("r", at_par, rng.choice([20, 30, 60]), at=at)
                rows.append(bid)
                lines.append("add %s %s %d %d" % (bid, at_par, at, sh.own[bid]))
                continue
            b = rng.choice(pool)
            if k < 0.7:
                sh.own[b] = rng.choice([0, 20, 30, 60, 120, 200])
                lines.append("size %s %d" % (b, sh.own[b]))
            elif k < 0.78 and b != focus:
                sh.drop(b)
                lines.append("drop %s" % b)
            elif k < 0.86:
                if b in sh.shut:
                    sh.shut.discard(b)
                    lines.append("open %s" % b)
                else:
                    sh.shut.add(b)
                    lines.append("shut %s" % b)
            elif k < 0.92:
                if b in sh.lift:
                    sh.lift.discard(b)
                    lines.append("sink %s" % b)
                else:
                    sh.lift.add(b)
                    lines.append("lift %s" % b)
            else:
                heads = [x for x in near if x in sh.pin]
                if heads:
                    h = rng.choice(heads)
                    sh.own[h] = rng.choice([20, 28, 40])
                    lines.append("size %s %d" % (h, sh.own[h]))


def fam_big(kind, rng, frames=BIG_FRAMES):
    sh, order, vh = (build_long if kind == "long" else build_wide)(rng)
    lines = ["view %d" % vh]
    for bid in order:
        fl = ["pin=%d" % sh.pin[bid]] if bid in sh.pin else []
        lines.append(" ".join(["box", bid, sh.par[bid], str(sh.own[bid])] + fl))
    lines.append("at 0")
    big_frames(rng, sh, vh, frames, lines)
    return lines


def fam_rare(rng):
    """The situations the other families reach only now and then, searched for directly: the
    old offset past the end of the new range, a later pass with nothing qualifying, and boxes
    of no height at the top of the view."""
    p = Pen(rng, rng.randint(80, 200))
    document(p, rng, sections=(2, 5), rows=(2, 6), head=0.9, sub=0.45, zero=0.2)
    p.start(lambda w: w.span() - rng.randint(0, 40))
    for f in range(rng.randint(10, 20)):
        k = rng.random()
        if k < 0.35:
            chosen = None
            for _ in range(10):
                cuts = [b for b in p.below() + p.inside() if b not in p.chain()]
                if not cuts:
                    break
                cand = ["drop %s" % b.id for b in rng.sample(cuts, min(len(cuts), rng.randint(1, 3)))]
                extra = candidates(p, rng)
                if extra and rng.random() < 0.6:
                    cand = extra[0] + cand
                after = []
                _s, _w, trace = p.trial(cand, after)
                if trace and p.s > after[0].span() and len(trace) >= 2:
                    chosen = cand
                    break
                chosen = chosen or cand
            p.frame(chosen or [])
        elif k < 0.6:
            # Grow something above the holder's top-level box by just enough that pinning that
            # box leaves it unstuck at the old offset; the adjustment then carries the view past
            # its stick line, and the pass after finds no box of the chain that qualifies.
            chain = p.chain()
            top = chain[-1] if chain else None
            above = [b for b in p.world.root.kids
                     if top is not None and b is not top and b.c > 0
                     and p.world.top(b) < p.world.top(top)]
            if top is not None and above:
                t = rng.randint(0, 30)
                g = p.s + t - p.world.top(top) + rng.randint(0, 20)
                b = rng.choice(above)
                p.frame(["size %s %d" % (b.id, b.own + max(0, g)), "pin %s %d" % (top.id, t)])
            else:
                reset(p, rng)
        elif k < 0.8:
            empties = [b for b, y, h in p.laid() if h == 0]
            if empties:
                b = rng.choice(empties)
                edits = ["to %d" % max(0, p.world.top(b) - p.band() - rng.randint(1, 20))]
                p.frame(edits)
                if b.pin is None and rng.random() < 0.5 and b.id in p.world.by:
                    p.frame(["pin %s %d" % (b.id, rng.randint(5, 30))])
            else:
                reset(p, rng)
        else:
            p.frame(search(p, rng, lambda tr: passes(tr)[0] >= 3))
    return p.lines


MAKERS = {
    "plain": fam_plain, "band": fam_band, "stick": fam_stick, "cycle": fam_cycle,
    "push": fam_push, "fall": fam_fall, "turn": fam_turn, "clamp": fam_clamp,
    "switch": fam_switch, "top": fam_top, "edge": fam_edge, "mix": fam_mix,
    "rare": fam_rare,
}


def programs(seed, per, small_only=False, big_frames_count=BIG_FRAMES):
    """[(family, name, lines)] for every family: `per` small programs each, BIG of each scale."""
    out = []
    for fam, big in FAMILIES:
        if big and small_only:
            continue
        for i in range(BIG if big else per):
            rng = random.Random("%s|%s|%d" % (seed, fam, i))
            if big:
                lines = fam_big(fam, rng, big_frames_count)
            else:
                lines = MAKERS[fam](rng)
            out.append((fam, "%s-%03d" % (fam, i), lines))
    return out


def graded(seed, per):
    """Every program the worker runs: the enumerated ones first, then the generated ones."""
    import cases
    progs = [{"fam": "hand", "name": n, "text": "\n".join(cases.prog(n)) + "\n"}
             for n in cases.ORDER]
    progs += [{"fam": f, "name": n, "text": "\n".join(lines) + "\n"}
              for f, n, lines in programs(seed, per)]
    return progs


def main(argv):
    seed = argv[argv.index("--seed") + 1]
    per = int(argv[argv.index("--per") + 1])
    out = argv[argv.index("--out") + 1]
    progs = graded(seed, per)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(progs, fh)


if __name__ == "__main__":
    main(sys.argv)
