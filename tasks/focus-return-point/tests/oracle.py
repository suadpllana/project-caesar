"""A second implementation of the focus rules, written from the brief and sharing no code
with the tree or the reference. Root-only in the verifier image.

Shape, deliberately different from the runtime's: the tree is flat dictionaries keyed by
widget id rather than linked node objects; every widget's position is recorded at the
moment it is dropped (the runtime reads it back off a detached parent instead); screens
are names with an explicit record of what stood underneath; and a landing is resolved by
a recursive function rather than a loop. The trail it produces is the focus after each
event, as strings, which is what the grader compares.
"""

BLOCK = frozenset(("hid", "off", "shut"))


class Sim:
    def __init__(self):
        self.par = {}      # wid -> parent wid (screen name for a top-level widget)
        self.kids = {}     # wid or screen -> [wid]
        self.fl = {}       # wid -> set of flags
        self.grp = {}      # wid -> group or None
        self.home = {}     # wid or screen -> screen name
        self.screens = []  # declared screens, in order
        self.stack = []    # screen names, last is top
        self.dead = set()  # popped screens
        self.lost = {}     # dropped wid -> (parent, index) at the drop
        self.focus = None
        self.ret = {}      # screen -> landing recorded when it went on top
        self.held = {}     # screen -> wid of the latest request made while not on top
        self.orig = None   # landing that focus was lost from
        self.mem = {}      # composite wid -> wid

    # --------------------------------------------------------------- tree

    def screen(self, nm):
        self.screens.append(nm)
        self.kids[nm] = []
        self.home[nm] = nm

    def widget(self, wid, parent, flags, grp, at=None):
        self.par[wid] = parent
        self.kids[wid] = []
        self.fl[wid] = set(flags)
        self.grp[wid] = grp
        self.home[wid] = self.home[parent]
        row = self.kids[parent]
        if at is None or at >= len(row):
            row.append(wid)
        else:
            row.insert(max(0, at), wid)

    def is_screen(self, key):
        return key in self.home and self.home[key] == key and key in self.screens

    def live(self, key):
        if self.is_screen(key):
            return key not in self.dead
        return key in self.par and key not in self.lost and self.home[key] not in self.dead

    def top(self):
        return self.stack[-1] if self.stack else None

    def chain(self, wid):
        """wid and every container above it, up to but not including the screen."""
        out = []
        cur = wid
        while cur is not None and not self.is_screen(cur):
            out.append(cur)
            cur = self.par.get(cur)
        return out

    def can(self, wid):
        if not self.live(wid) or self.home[wid] != self.top() or "foc" not in self.fl[wid]:
            return False
        return all(not (self.fl[c] & BLOCK) for c in self.chain(wid))

    def comp_of(self, wid):
        for c in self.chain(wid)[1:]:
            if "comp" in self.fl[c]:
                return c
        return None

    def preorder(self, key):
        out = [key]
        for k in self.kids[key]:
            out.extend(self.preorder(k))
        return out

    def members(self, comp):
        return [w for w in self.preorder(comp)[1:] if self.can(w)]

    def stops(self):
        t = self.top()
        if t is None:
            return []
        seq = self.preorder(t)[1:]
        lead = {}
        for w in seq:
            g = self.grp[w]
            if g is None or not self.can(w):
                continue
            if g not in lead or ("sel" in self.fl[w] and "sel" not in self.fl[lead[g]]):
                lead[g] = w
        out = []
        for w in seq:
            if self.comp_of(w) is not None:
                continue
            if "comp" in self.fl[w]:
                if self.members(w):
                    out.append(w)
                continue
            if self.can(w) and (self.grp[w] is None or lead[self.grp[w]] == w):
                out.append(w)
        return out

    # ------------------------------------------------------------ landings

    def where(self, wid):
        """The point a gone widget stood at; a gone screen root resolves to its return."""
        if self.is_screen(wid):
            return self.ret.get(wid)
        if wid in self.lost:
            p, i = self.lost[wid]
            return ("p", p, i)
        return ("p", self.par[wid], self.kids[self.par[wid]].index(wid))

    def fix(self, t):
        if t is None:
            return None
        if t[0] == "w":
            return t if self.live(t[1]) else self.fix(self.where(t[1]))
        return t if self.live(t[1]) else self.fix(self.where(t[1]))

    def land(self, wid):
        self.focus = wid
        self.orig = None
        c = self.comp_of(wid)
        if c is not None:
            self.mem[c] = wid

    def lose(self, at):
        self.focus = None
        self.orig = at

    def settle(self, t):
        r = self.fix(t)
        if r is not None and r[0] == "w" and self.can(r[1]):
            self.land(r[1])
        else:
            self.lose(r)

    def standing(self):
        return ("w", self.focus) if self.focus is not None else self.orig

    def go(self, stop):
        if "comp" in self.fl[stop]:
            m = self.mem.get(stop)
            room = self.members(stop)
            stop = m if (m in room and self.comp_of(m) == stop) else room[0]
        self.land(stop)

    # -------------------------------------------------------------- events

    def key(self, fwd):
        st = self.stops()
        if not st:
            return
        seq = self.preorder(self.top())
        pos = {w: i for i, w in enumerate(seq)}
        r = self.fix(self.standing())
        if r is not None and r[0] == "w" and r[1] in pos:
            c = self.comp_of(r[1])
            lo = pos[r[1]]
            hi = pos[c] if c is not None else lo
            cand = [s for s in st if pos[s] > lo] if fwd else [s for s in st if pos[s] < hi]
        elif r is not None and r[0] == "p" and r[1] in pos:
            p, i = r[1], r[2]
            row = self.kids[p]
            if i < len(row):
                edge = pos[row[i]]
            else:
                edge = pos[self.preorder(p)[-1]] + 1
            cand = [s for s in st if pos[s] >= edge] if fwd else [s for s in st if pos[s] < edge]
        else:
            cand = []
        if not cand:
            cand = st
        self.go(cand[0] if fwd else cand[-1])

    def arrow(self, fwd):
        f = self.focus
        if f is None:
            return
        c = self.comp_of(f)
        if c is None:
            return
        room = self.members(c)
        if f not in room:
            return
        i = room.index(f) + (1 if fwd else -1)
        if 0 <= i < len(room):
            self.land(room[i])

    def want(self, wid):
        if wid not in self.par or not self.live(wid):
            return
        s = self.home[wid]
        if s == self.top():
            if self.can(wid):
                self.land(wid)
        elif s not in self.dead:
            self.held[s] = wid

    def arrive(self, s):
        if s in self.held:
            self.settle(("w", self.held.pop(s)))
            return
        for w in self.preorder(s)[1:]:
            if "auto" in self.fl[w] and self.can(w):
                self.land(w)
                return
        st = self.stops()
        if st:
            self.go(st[0])
        else:
            self.lose(("p", s, 0))

    def push(self, s):
        self.ret[s] = self.standing()
        self.stack.append(s)
        self.arrive(s)

    def pop(self, s):
        was_top = self.stack and self.stack[-1] == s
        if s in self.stack:
            self.stack.remove(s)
        self.dead.add(s)
        if not was_top:
            return
        t = self.top()
        if t is None:
            self.lose(None)
        elif t in self.held:
            self.settle(("w", self.held.pop(t)))
        else:
            self.settle(self.ret.get(s))

    def drop(self, wid):
        p = self.par[wid]
        i = self.kids[p].index(wid)
        self.kids[p].remove(wid)
        for w in self.preorder(wid):
            q = self.par[w]
            self.lost[w] = (q, self.kids[q].index(w)) if w != wid else (p, i)

    def check(self):
        if self.focus is not None and not self.can(self.focus):
            self.lose(("w", self.focus))

    def event(self, toks):
        k = toks[0]
        if k == "tab":
            self.key(True)
        elif k == "back":
            self.key(False)
        elif k == "next":
            self.arrow(True)
        elif k == "prev":
            self.arrow(False)
        elif k == "want":
            self.want(toks[1])
        elif k == "push":
            self.push(toks[1])
        elif k == "pop":
            self.pop(toks[1])
        else:
            self.mutate(toks)
            self.check()

    def mutate(self, toks):
        k = toks[0]
        if k == "add":
            fl, grp = split_flags(toks[4:])
            self.widget(toks[1], toks[2], fl, grp, int(toks[3]))
            return
        w = toks[1]
        if w not in self.par or w in self.lost:
            return
        if k == "drop":
            self.drop(w)
        elif k in ("hide", "off", "shut"):
            self.fl[w].add({"hide": "hid", "off": "off", "shut": "shut"}[k])
        elif k in ("show", "on", "open"):
            self.fl[w].discard({"show": "hid", "on": "off", "open": "shut"}[k])
        elif k == "move":
            self.kids[self.par[w]].remove(w)
            self.par[w] = toks[2]
            row = self.kids[toks[2]]
            at = int(toks[3])
            if at >= len(row):
                row.append(w)
            else:
                row.insert(max(0, at), w)
        elif k == "pick":
            g = self.grp[w]
            if g is not None:
                for o in self.par:
                    if self.grp[o] == g and self.home[o] == self.home[w]:
                        self.fl[o].discard("sel")
                self.fl[w].add("sel")


def split_flags(toks):
    fl, grp = [], None
    for t in toks:
        if t.startswith("grp="):
            grp = t[4:]
        else:
            fl.append(t)
    return fl, grp


def solve(text):
    """The trail: focus after each event, as a list of strings."""
    sim = Sim()
    out = []
    for raw in text.split("\n"):
        toks = raw.split()
        if not toks:
            continue
        if toks[0] == "screen":
            sim.screen(toks[1])
        elif toks[0] == "w":
            fl, grp = split_flags(toks[3:])
            sim.widget(toks[1], toks[2], fl, grp)
        else:
            sim.event(toks)
            out.append(sim.focus if sim.focus is not None else "none")
    return out
