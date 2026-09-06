from ui import mem, reach
from ui.keep import Keep


class Pol:
    def __init__(self, ui):
        self.keep = Keep()
        self.mem = {}

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
            self.check(ui)

    def check(self, ui):
        if ui.fo is not None and not reach.can(ui, ui.fo):
            ui.land(None)

    def first(self, ui):
        st = reach.stops(ui)
        if st:
            self.take(ui, st[0], 1)
        else:
            ui.land(None)

    def push(self, ui, s):
        self.keep.push(s, ui.fo)
        self.first(ui)

    def pop(self, ui, s, at):
        back = self.keep.pop(s)
        if at is None or at != len(ui.st):
            return
        if reach.top(ui) is None:
            ui.land(None)
        elif back is not None and reach.can(ui, back):
            ui.land(back)
        else:
            self.first(ui)

    def want(self, ui, nd):
        if nd is not None and nd.scr is reach.top(ui) and reach.can(ui, nd):
            ui.land(nd)

    def take(self, ui, stop, d):
        if "comp" in stop.fl:
            stop = mem.enter(ui, self.mem, stop, d)
        ui.land(stop)

    def walk(self, ui, d):
        st = reach.stops(ui)
        if not st:
            return
        f = ui.fo
        if f is None:
            self.take(ui, st[0] if d > 0 else st[-1], d)
            return
        at = {nd: i for i, nd in enumerate(reach.order(ui))}
        c = reach.within(f)
        lo = at[f]
        hi = at[c] if c is not None else at[f]
        pick = ([s for s in st if at[s] > lo] if d > 0 else
                [s for s in st if at[s] < hi])
        if not pick:
            pick = [st[0] if d > 0 else st[-1]]
        self.take(ui, pick[0] if d > 0 else pick[-1], d)

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
        nd = room[(room.index(f) + d) % len(room)]
        ui.land(nd)
        mem.note(self.mem, nd)
