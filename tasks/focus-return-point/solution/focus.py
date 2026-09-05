"""The focus policy: what each event does to focus.

The rules are the ones the brief states. The order of business on every event is the
same: keys and requests move focus directly; a push records where focus was and lands on
the new screen; a pop of the screen on top resolves a deferred landing; and any change to
the tree is followed by one question, whether the widget holding focus can still hold it,
answered by reach.can against the tree as it now is.

Every landing that has to wait - a return record, a held request, the place focus was
lost - goes through keep.spot at the moment it is needed and never earlier.
"""

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
            # A place inside a composite stands where the composite stands going back,
            # exactly as a widget inside one does.
            c = p if "comp" in p.fl else reach.within(p)
            hi = at[c] if c is not None and c in at else pos
            pick = ([s for s in st if at[s] >= pos] if d > 0 else
                    [s for s in st if at[s] < hi])
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
