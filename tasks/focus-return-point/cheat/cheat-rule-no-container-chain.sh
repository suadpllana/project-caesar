#!/bin/bash
# cheat: no-container-chain
# a point whose container has gone resolves to nothing instead of the container's place
set -euo pipefail
mkdir -p /app/ui
cat > /app/ui/focus.py <<'PYEOF'
from ui import mem, reach
from ui.node import Nd
from ui.keep import Keep


class Pol:
    def __init__(self, ui):
        self.keep = Keep()
        self.mem = {}

    # ------------------------------------------------------------- events

    def on(self, ui, ev):
        k = ev.k
        if k == "tab":
            self.walk(ui, 1)
        elif k == "back":
            self.walk(ui, -1)
        elif k in ("next", "prev"):
            self.arrow(ui, 1 if k == "next" else -1)
        elif k == "want":
            self.want(ui, ev.w)
        elif k == "push":
            self.push(ui, ev.s)
        elif k == "pop":
            self.pop(ui, ev.s, ev.at)
        else:
            if k == "drop" and ev.w is not None:
                self.keep.drop(ev.w, ev.at)
            self.check(ui)

    # ------------------------------------------------------------- landing

    def put(self, ui, nd):
        ui.land(nd)
        mem.note(self.mem, nd)
        self.keep.orig = None

    def lose(self, ui, where):
        ui.land(None)
        self.keep.orig = where

    def settle(self, ui, tgt):
        r = self.keep.spot(ui, tgt)
        if isinstance(r, Nd) and reach.can(ui, r):
            self.put(ui, r)
        else:
            self.lose(ui, r)

    def here(self, ui):
        return ui.fo if ui.fo is not None else self.keep.orig

    def check(self, ui):
        if ui.fo is not None and not reach.can(ui, ui.fo):
            self.lose(ui, ui.fo)

    # ------------------------------------------------------------- screens

    def push(self, ui, s):
        self.keep.ret[s] = self.here(ui)
        if s in self.keep.held:
            self.settle(ui, self.keep.held.pop(s))
            return
        for nd in reach.order(ui):
            if "auto" in nd.fl and reach.can(ui, nd):
                self.put(ui, nd)
                return
        st = reach.stops(ui)
        if st:
            self.take(ui, st[0])
        else:
            self.lose(ui, ("pt", s.root, 0))

    def pop(self, ui, s, at):
        if at is None or at != len(ui.st):
            return
        now = reach.top(ui)
        if now is None:
            self.lose(ui, None)
        elif now in self.keep.held:
            self.settle(ui, self.keep.held.pop(now))
        else:
            self.settle(ui, self.keep.ret.get(s))

    # ------------------------------------------------------------- requests

    def want(self, ui, nd):
        if nd is None:
            return
        if nd.scr is reach.top(ui):
            if reach.can(ui, nd):
                self.put(ui, nd)
        elif nd.scr.nm in ui.scr:
            self.keep.held[nd.scr] = nd

    # ------------------------------------------------------------- keys

    def take(self, ui, stop):
        if "comp" in stop.fl:
            stop = mem.enter(ui, self.mem, stop)
        self.put(ui, stop)

    def walk(self, ui, d):
        st = reach.stops(ui)
        if not st:
            return
        ordr = reach.order(ui)
        at = {nd: i for i, nd in enumerate(ordr)}
        r = self.keep.spot(ui, self.here(ui))
        if isinstance(r, Nd) and r in at:
            # From a widget, whether it holds focus or is the place focus was lost:
            # strictly after it going forward, strictly before it going back, and going
            # back from inside a composite means before the composite.
            c = reach.within(r)
            lo = at[r]
            hi = at[c] if c is not None and c in at else at[r]
            pick = ([s for s in st if at[s] > lo] if d > 0 else
                    [s for s in st if at[s] < hi])
        elif isinstance(r, tuple) and r[1] in at:
            # From a point: the first stop at or after it, or the last stop before it.
            p, i = r[1], r[2]
            if i < len(p.kids):
                pos = at[p.kids[i]]
            else:
                pos = max(at[n] for n in ordr if n is p or reach.under(n, p)) + 1
            pick = ([s for s in st if at[s] >= pos] if d > 0 else
                    [s for s in st if at[s] < pos])
        else:
            pick = st if d > 0 else st[::-1]
            pick = [pick[0]]
        if not pick:
            pick = [st[0] if d > 0 else st[-1]]
        self.take(ui, pick[0] if d > 0 else pick[-1])

    def arrow(self, ui, d):
        f = ui.fo
        if f is None:
            return
        c = reach.within(f)
        if c is None:
            return
        room = reach.inside(ui, c)
        if f not in room:
            return
        i = room.index(f) + d
        if 0 <= i < len(room):
            self.put(ui, room[i])
PYEOF
cat > /app/ui/keep.py <<'PYEOF'
from ui import reach
from ui.node import Nd


class Keep:
    def __init__(self):
        self.ret = {}
        self.held = {}
        self.orig = None
        self.gone = {}

    def drop(self, nd, at):
        # Only the root of a dropped subtree needs recording: everything below it still
        # hangs off a detached parent whose child list is intact, so its own place can
        # be read off the parent when it is asked for.
        self.gone[nd] = (nd.par, at)

    def place(self, nd):
        """The point a gone widget stood at. For a screen root, the screen's return."""
        if nd.par is None:
            return self.ret.get(nd.scr)
        if nd in self.gone:
            p, at = self.gone[nd]
            return ("pt", p, at)
        return ("pt", nd.par, nd.par.kids.index(nd))

    def spot(self, ui, tgt):
        """Resolve a landing against the tree as it is now.

        Returns a live widget (which may or may not be able to take focus - the caller
        decides), a point whose container is live, or None.
        """
        while tgt is not None:
            if isinstance(tgt, Nd):
                if reach.alive(ui, tgt):
                    return tgt
                tgt = self.place(tgt)
            else:
                if reach.alive(ui, tgt[1]):
                    return tgt
                return None
        return None
PYEOF
cat > /app/ui/reach.py <<'PYEOF'
BLOCK = ("hid", "off", "shut")


def top(ui):
    return ui.st[-1] if ui.st else None


def alive(ui, nd):
    # A screen root is alive while its screen has not been popped; every other widget is
    # alive while the core still lists it. A dropped subtree and a popped screen are both
    # gone from that list, which is what makes the two cases one case in keep.py.
    if nd.par is None:
        return nd.scr.nm in ui.scr
    return nd.wid in ui.nd


def can(ui, nd):
    if not alive(ui, nd) or nd.scr is not top(ui) or "foc" not in nd.fl:
        return False
    cur = nd
    while cur is not None:
        if cur.fl & set(BLOCK):
            return False
        cur = cur.par
    return True


def order(ui):
    """Every widget of the screen on top, in pre-order, the root first."""
    s = top(ui)
    out = []
    if s is None:
        return out

    def walk(nd):
        out.append(nd)
        for k in nd.kids:
            walk(k)

    walk(s.root)
    return out


def within(nd):
    """The composite a widget sits inside, or None. Composites do not nest."""
    cur = nd.par
    while cur is not None:
        if "comp" in cur.fl:
            return cur
        cur = cur.par
    return None


def inside(ui, comp):
    """The focusable descendants of a composite, in pre-order."""
    out = []

    def walk(nd):
        for k in nd.kids:
            if can(ui, k):
                out.append(k)
            walk(k)

    walk(comp)
    return out


def stops(ui):
    """The tab stops of the screen on top, in tree order.

    A composite is one stop, standing at its own position, as long as something inside
    it can take focus; nothing inside a composite is a stop in its own right. Of a group,
    the selected member is the stop when it can take focus, otherwise the first member
    that can. Everything else that can take focus is a stop.
    """
    ordr = order(ui)
    lead = {}
    for nd in ordr:
        if nd.grp is None or not can(ui, nd):
            continue
        if nd.grp not in lead or ("sel" in nd.fl and "sel" not in lead[nd.grp].fl):
            lead[nd.grp] = nd
    out = []
    skip = None
    for nd in ordr:
        if skip is not None:
            if nd is skip or under(nd, skip):
                continue
            skip = None
        if "comp" in nd.fl:
            if inside(ui, nd):
                out.append(nd)
            skip = nd
            continue
        if not can(ui, nd):
            continue
        if nd.grp is not None and lead.get(nd.grp) is not nd:
            continue
        out.append(nd)
    return out


def under(nd, anc):
    cur = nd.par
    while cur is not None:
        if cur is anc:
            return True
        cur = cur.par
    return False
PYEOF
cat > /app/ui/mem.py <<'PYEOF'
from ui import reach


def note(mem, nd):
    c = reach.within(nd)
    if c is not None:
        mem[c] = nd


def enter(ui, mem, comp):
    m = mem.get(comp)
    if m is not None and reach.within(m) is comp and reach.can(ui, m):
        return m
    room = reach.inside(ui, comp)
    return room[0] if room else None
PYEOF
