"""Generated scripts, built from the run nonce inside the verifier after the agent has
finished. Deterministic across processes: every collection is sorted before it is drawn
from, and the only randomness is a random.Random seeded from a digest of the nonce and
the script index.

The generator never runs the runtime. It keeps just enough of its own bookkeeping to emit
scripts the rules can grade: which screens have been pushed and popped, which widgets are
still in the tree, which widget was last asked for focus. Beyond that it does not know
where focus is, and it does not need to.
"""

import hashlib
import random

MUT = ("hide", "show", "off", "on", "shut", "open", "drop", "move", "add", "pick")


def seed_for(nonce, i):
    h = hashlib.sha256(("%s:%d" % (nonce, i)).encode("utf-8")).hexdigest()
    return int(h[:16], 16)


class Plan:
    def __init__(self, rng):
        self.rng = rng
        self.lines = []
        self.screens = []
        self.widgets = {}      # wid -> dict(scr, par, fl, grp)
        self.kids = {}         # container -> [wid]
        self.pushed = []       # screens currently on the stack, in order
        self.unpushed = []
        self.popped = set()
        self.nw = 0
        self.ng = 0

    # ----------------------------------------------------------- building

    def fresh(self):
        self.nw += 1
        return "w%d" % self.nw

    def widget(self, scr, par, fl, grp=None):
        wid = self.fresh()
        self.widgets[wid] = {"scr": scr, "par": par, "fl": list(fl), "grp": grp}
        self.kids[wid] = []
        self.kids[par].append(wid)
        tail = list(fl) + (["grp=%s" % grp] if grp else [])
        self.lines.append(" ".join(["w", wid, par] + tail))
        return wid

    def initial(self):
        rng = self.rng
        return [f for f, p in (("hid", 0.08), ("off", 0.08), ("shut", 0.04)) if rng.random() < p]

    def screen(self, nm):
        rng = self.rng
        self.screens.append(nm)
        self.kids[nm] = []
        self.lines.append("screen %s" % nm)
        n = rng.randint(2, 4)
        for _ in range(n):
            kind = rng.random()
            if kind < 0.28:
                box = self.widget(nm, nm, self.initial())
                for _ in range(rng.randint(1, 3)):
                    self.widget(nm, box, ["foc"] + self.initial())
            elif kind < 0.5:
                comp = self.widget(nm, nm, ["comp"] + self.initial())
                for _ in range(rng.randint(2, 4)):
                    self.widget(nm, comp, ["foc"] + self.initial())
            elif kind < 0.68:
                self.ng += 1
                g = "g%d" % self.ng
                k = rng.randint(2, 3)
                sel = rng.randrange(k) if rng.random() < 0.7 else -1
                for i in range(k):
                    fl = ["foc"] + (["sel"] if i == sel else []) + self.initial()
                    self.widget(nm, nm, fl, g)
            else:
                self.widget(nm, nm, ["foc"] + self.initial())
        seq = self.on(nm)
        if seq and rng.random() < 0.45:
            w = rng.choice(seq)
            self.widgets[w]["fl"].append("auto")
            i = [k for k, ln in enumerate(self.lines) if ln.split()[1:2] == [w]][0]
            self.lines[i] += " auto"

    # ----------------------------------------------------------- queries

    def on(self, scr):
        return sorted(w for w, d in self.widgets.items() if d["scr"] == scr)

    def under(self, w, anc):
        cur = self.widgets[w]["par"]
        while cur in self.widgets:
            if cur == anc:
                return True
            cur = self.widgets[cur]["par"]
        return cur == anc

    def top(self):
        return self.pushed[-1] if self.pushed else None

    def live_screens(self):
        return sorted(s for s in self.screens if s not in self.popped)

    def forget(self, w):
        for k in list(self.kids.get(w, [])):
            self.forget(k)
        self.kids.pop(w, None)
        d = self.widgets.pop(w, None)
        if d is not None and d["par"] in self.kids:
            self.kids[d["par"]].remove(w)

    # ----------------------------------------------------------- events

    def emit(self, *toks):
        self.lines.append(" ".join(str(t) for t in toks))

    def push(self, nm=None):
        if nm is None:
            if not self.unpushed:
                return False
            nm = self.unpushed[0]
        self.unpushed.remove(nm)
        self.pushed.append(nm)
        self.emit("push", nm)
        return True

    def pop(self, nm):
        self.pushed.remove(nm)
        self.popped.add(nm)
        for w in self.on(nm):
            self.forget(w)
        self.emit("pop", nm)

    def pop_some(self, out_of_order):
        if not self.pushed:
            return False
        if out_of_order and len(self.pushed) > 1:
            self.pop(self.rng.choice(self.pushed[:-1]))
        else:
            self.pop(self.pushed[-1])
        return True

    def mutate(self):
        rng = self.rng
        pool = sorted(w for w in self.widgets)
        if not pool:
            return
        k = rng.choice(MUT)
        w = rng.choice(pool)
        if k == "add":
            scr = self.widgets[w]["scr"]
            hosts = [scr] + [x for x in self.on(scr) if "foc" not in self.widgets[x]["fl"]
                             or self.kids[x]]
            host = rng.choice(sorted(hosts))
            at = rng.randint(0, len(self.kids[host]))
            wid = self.fresh()
            fl = ["foc"]
            grp = None
            if self.widgets.get(host, {}).get("grp") is None and rng.random() < 0.15:
                gs = sorted({self.widgets[x]["grp"] for x in self.on(scr)
                             if self.widgets[x]["grp"] and self.widgets[x]["par"] == host})
                if gs:
                    grp = rng.choice(gs)
            self.widgets[wid] = {"scr": scr, "par": host, "fl": fl, "grp": grp}
            self.kids[wid] = []
            self.kids[host].insert(min(at, len(self.kids[host])), wid)
            self.emit("add", wid, host, at, *(fl + (["grp=%s" % grp] if grp else [])))
        elif k == "move":
            scr = self.widgets[w]["scr"]
            hosts = [scr] + [x for x in self.on(scr)
                             if x != w and not self.under(x, w) and "comp" not in self.widgets[x]["fl"]
                             and "foc" not in self.widgets[x]["fl"]]
            host = rng.choice(sorted(hosts))
            at = rng.randint(0, 3)
            self.kids[self.widgets[w]["par"]].remove(w)
            self.widgets[w]["par"] = host
            self.kids[host].insert(min(at, len(self.kids[host])), w)
            self.emit("move", w, host, at)
        elif k == "drop":
            if len(self.on(self.widgets[w]["scr"])) <= 2:
                return
            self.forget(w)
            self.emit("drop", w)
            if rng.random() < 0.5:
                self.emit(rng.choice(("tab", "back")))
        elif k == "pick":
            if self.widgets[w]["grp"] is None:
                return
            self.emit("pick", w)
        else:
            self.emit(k, w)
            if k in ("hide", "off", "shut") and rng.random() < 0.5:
                self.emit(rng.choice(("tab", "back")))

    def request(self, prefer_below):
        rng = self.rng
        cands = sorted(self.widgets)
        if prefer_below and self.pushed[:-1] or (prefer_below and self.unpushed):
            below = [w for w in cands if self.widgets[w]["scr"] != self.top()
                     and self.widgets[w]["scr"] not in self.popped]
            if below:
                cands = below
        if not cands:
            return
        w = rng.choice(cands)
        self.emit("want", w)

    def toggle(self, w, undo):
        rng = self.rng
        pair = rng.choice((("hide", "show"), ("off", "on"), ("shut", "open")))
        target = w
        if rng.random() < 0.35:
            par = self.widgets[w]["par"]
            if par in self.widgets:
                target = par
        self.emit(pair[0], target)
        if undo:
            self.emit(pair[1], target)

    def stack_pattern(self):
        """Three screens up, one from the middle popped, then the top popped, so the
        return record above it points into a screen that has gone."""
        rng = self.rng
        while len(self.pushed) < 3 and self.unpushed:
            if rng.random() < 0.7:
                seq = [w for w in self.on(self.top()) if "foc" in self.widgets[w]["fl"]]
                if seq:
                    self.emit("want", rng.choice(seq))
            self.push()
        if len(self.pushed) < 3:
            return
        victim = rng.choice(self.pushed[1:-1])
        above = self.pushed[self.pushed.index(victim) + 1]
        if rng.random() < 0.5:
            seq = [w for w in self.on(above) if "foc" in self.widgets[w]["fl"]]
            if seq:
                self.emit("want", rng.choice(seq))
        self.pop(victim)
        if rng.random() < 0.85:
            self.pop(self.pushed[-1])

    def box_pattern(self):
        """Focus inside a container, then the container dropped, under a push or not."""
        rng = self.rng
        t = self.top()
        if t is None:
            return
        boxes = [w for w in self.on(t) if "foc" not in self.widgets[w]["fl"]
                 and "comp" not in self.widgets[w]["fl"]
                 and any("foc" in self.widgets[k]["fl"] for k in self.kids[w])]
        if not boxes or len(self.on(t)) <= 3:
            return
        box = rng.choice(boxes)
        inner = [k for k in self.kids[box] if "foc" in self.widgets[k]["fl"]]
        self.emit("want", rng.choice(inner))
        pushed = False
        if self.unpushed and rng.random() < 0.5:
            self.push()
            pushed = True
        self.forget(box)
        self.emit("drop", box)
        if pushed and rng.random() < 0.8:
            self.pop(self.pushed[-1])
        elif not pushed:
            self.emit(rng.choice(("tab", "back")))

    def sibling_pattern(self):
        """Focus lost by a drop, then a sibling before the place removed or one inserted
        at it, then a key - the case where a place that moved would show."""
        rng = self.rng
        t = self.top()
        if t is None:
            return
        seq = [w for w in self.on(t) if "foc" in self.widgets[w]["fl"]
               and self.kids[self.widgets[w]["par"]].index(w) > 0]
        if not seq or len(self.on(t)) <= 3:
            return
        w = rng.choice(seq)
        par = self.widgets[w]["par"]
        at = self.kids[par].index(w)
        self.emit("want", w)
        self.forget(w)
        self.emit("drop", w)
        r = rng.random()
        if r < 0.5:
            earlier = self.kids[par][rng.randrange(at)]
            self.forget(earlier)
            self.emit("drop", earlier)
        else:
            wid = self.fresh()
            self.widgets[wid] = {"scr": t, "par": par, "fl": ["foc"], "grp": None}
            self.kids[wid] = []
            spot = rng.choice((0, at))
            self.kids[par].insert(spot, wid)
            self.emit("add", wid, par, spot, "foc")
        self.emit(rng.choice(("tab", "back")))

    def hold_pattern(self):
        """A request for a screen that is not on top, then the target disturbed."""
        rng = self.rng
        below = [s for s in self.live_screens() if s != self.top()]
        if not below:
            return
        s = rng.choice(below)
        seq = [w for w in self.on(s) if "foc" in self.widgets[w]["fl"]]
        if not seq:
            return
        w = rng.choice(seq)
        self.emit("want", w)
        r = rng.random()
        if r < 0.4:
            self.toggle(w, undo=True)
        elif r < 0.7:
            self.toggle(w, undo=False)
        elif r < 0.8 and len(self.on(s)) > 2:
            self.forget(w)
            self.emit("drop", w)
        # Bring that screen back on top soon, so the request is answered while it is
        # still the latest one made for it.
        if s in self.pushed and rng.random() < 0.7:
            while self.pushed and self.pushed[-1] != s:
                self.pop(self.pushed[-1])
        elif s in self.unpushed and rng.random() < 0.5:
            self.push(s)

    def return_pattern(self):
        """Focus on a widget, a push over it, the widget disturbed, the screen popped."""
        rng = self.rng
        t = self.top()
        if t is None or not self.unpushed:
            return
        seq = [w for w in self.on(t) if "foc" in self.widgets[w]["fl"]]
        if not seq:
            return
        w = rng.choice(seq)
        self.emit("want", w)
        self.push()
        for _ in range(rng.randint(0, 2)):
            self.emit(rng.choice(("tab", "back")))
        r = rng.random()
        if r < 0.4:
            self.toggle(w, undo=True)
        elif r < 0.7:
            self.toggle(w, undo=False)
        elif len(self.on(t)) > 2:
            self.forget(w)
            self.emit("drop", w)
        if rng.random() < 0.6:
            self.pop(self.pushed[-1])

    def build(self):
        rng = self.rng
        for i in range(rng.randint(3, 5)):
            self.screen("s%d" % (i + 1))
        self.unpushed = list(self.screens)
        self.push()
        want_ooo = rng.random() < 0.55
        n = rng.randint(22, 52)
        while n > 0:
            n -= 1
            r = rng.random()
            if r < 0.30:
                self.emit(rng.choice(("tab", "tab", "back")))
            elif r < 0.38:
                self.emit(rng.choice(("next", "prev")))
            elif r < 0.50:
                self.request(prefer_below=rng.random() < 0.5)
            elif r < 0.66:
                self.mutate()
            elif r < 0.73:
                self.hold_pattern()
            elif r < 0.80:
                self.return_pattern()
            elif r < 0.83:
                self.stack_pattern()
            elif r < 0.87:
                self.box_pattern()
            elif r < 0.92:
                self.sibling_pattern()
            elif r < 0.95:
                if not self.push():
                    self.pop_some(want_ooo and rng.random() < 0.6)
            else:
                if not self.pop_some(want_ooo and rng.random() < 0.6):
                    self.push()
            if not self.pushed and not self.unpushed:
                break
        while self.pushed and rng.random() < 0.7:
            self.pop_some(want_ooo and rng.random() < 0.4)
        return "\n".join(self.lines) + "\n"


def text(nonce, i):
    return Plan(random.Random(seed_for(nonce, i))).build()


def batch(nonce, n):
    return [("g%04d" % i, text(nonce, i)) for i in range(n)]
