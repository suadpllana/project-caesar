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
            c = p if "comp" in self.fl.get(p, set()) else self.comp_of(p)
            back_edge = pos[c] if c is not None and c in pos else edge
            cand = [s for s in st if pos[s] >= edge] if fwd else [s for s in st if pos[s] < back_edge]
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



class ScopeSim(Sim):
    """Independent flat-tree model of the proposed nested navigation contract."""

    def scope_rows(self, owner):
        seq = self.preorder(owner)[1:]
        scope = None if self.is_screen(owner) else owner
        visible = [w for w in seq if self.comp_of(w) == scope]
        groups = {}
        for w in visible:
            if self.grp[w] is not None and self.can(w):
                groups.setdefault(self.grp[w], []).append(w)
        reps = {}
        for g, members in groups.items():
            selected = [w for w in members if "sel" in self.fl[w]]
            reps[g] = (selected or members)[0]
        return [w for w in visible
                if (bool(self.members(w)) if "comp" in self.fl[w]
                    else self.can(w) and (self.grp[w] is None or reps[self.grp[w]] == w))]

    def stops(self):
        return self.scope_rows(self.top()) if self.top() is not None else []

    def land(self, wid):
        self.focus = wid
        self.orig = None
        path = [w for w in self.chain(wid)[1:] if "comp" in self.fl[w]]
        for i, owner in enumerate(path):
            self.mem[owner] = wid if i == 0 else path[i - 1]

    def descend(self, comp):
        remembered = self.mem.get(comp)
        if remembered is not None and self.live(remembered) and self.comp_of(remembered) == comp:
            if "comp" in self.fl[remembered]:
                if self.members(remembered):
                    return self.descend(remembered)
            elif self.can(remembered):
                return remembered
        first = self.scope_rows(comp)[0]
        return self.descend(first) if "comp" in self.fl[first] else first

    def go(self, stop):
        self.land(self.descend(stop) if "comp" in self.fl[stop] else stop)

    def key(self, fwd):
        stops = self.stops()
        if not stops:
            return
        order = self.preorder(self.top())
        pos = {w: i for i, w in enumerate(order)}
        point = self.fix(self.standing())
        choices = []
        if point is not None:
            kind, w = point[:2]
            owners = [a for a in self.chain(w) if "comp" in self.fl[a]]
            if owners:
                boundary = pos[owners[-1]]
                choices = [s for s in stops if (pos[s] > boundary if fwd else pos[s] < boundary)]
            elif kind == "w":
                choices = [s for s in stops if (pos[s] > pos[w] if fwd else pos[s] < pos[w])]
            else:
                idx = point[2]
                children = self.kids[w]
                boundary = pos[children[idx]] if idx < len(children) else pos[self.preorder(w)[-1]] + 1
                choices = [s for s in stops if (pos[s] >= boundary if fwd else pos[s] < boundary)]
        self.go((choices or stops)[0 if fwd else -1])

    def arrow(self, fwd):
        if self.focus is None:
            return
        pos = {w: i for i, w in enumerate(self.preorder(self.top()))}
        pivot = self.focus
        for owner in [w for w in self.chain(self.focus)[1:] if "comp" in self.fl[w]]:
            candidates = [w for w in self.scope_rows(owner)
                          if (pos[w] > pos[pivot] if fwd else pos[w] < pos[pivot])]
            if candidates:
                self.go(candidates[0 if fwd else -1])
                return
            pivot = owner


def split_flags(toks):
    fl, grp = [], None
    for t in toks:
        if t.startswith("grp="):
            grp = t[4:]
        else:
            fl.append(t)
    return fl, grp


class InstanceSim(ScopeSim):
    """Flat records use monotonically allocated handles, separate from script names."""

    def __init__(self):
        super().__init__()
        self.names = {}
        self.labels = {}
        self.serial = 0

    def feed(self, toks):
        toks = list(toks)
        kind = toks[0]
        if kind == "screen":
            self.screen(toks[1])
        elif kind in ("w", "add"):
            name = toks[1]
            old = self.names.get(name)
            assert old is None or not self.live(old), "duplicate live widget id"
            self.serial += 1
            handle = ("widget", self.serial)
            parent = self.names.get(toks[2], toks[2])
            flags, group = split_flags(toks[3:] if kind == "w" else toks[4:])
            self.widget(handle, parent, flags, group,
                        None if kind == "w" else int(toks[3]))
            self.names[name] = handle
            self.labels[handle] = name
            if kind == "add":
                self.check()
        else:
            if kind not in ("push", "pop") and len(toks) > 1:
                toks[1] = self.names.get(toks[1], toks[1])
            if kind == "move":
                toks[2] = self.names.get(toks[2], toks[2])
            self.event(toks)


class BufferedSim(InstanceSim):
    """Savepoints retain flat records; focus intents run against the committed tree.

    Allocated handles and their public labels outlive an aborted allocation. All
    structural tables, including the name map and deletion positions, roll back.
    Focus, return records, pending requests and memories need no snapshot: no
    operation inside an open savepoint is allowed to change them.
    """

    KEYS = frozenset(("tab", "back", "next", "prev"))

    def __init__(self):
        super().__init__()
        self.frames = []

    def saved_tree(self):
        return {
            "par": dict(self.par),
            "kids": {w: list(row) for w, row in self.kids.items()},
            "fl": {w: set(flags) for w, flags in self.fl.items()},
            "grp": dict(self.grp),
            "home": dict(self.home),
            "lost": dict(self.lost),
            "names": dict(self.names),
        }

    def check(self):
        if not self.frames:
            super().check()

    def bound_want(self, wid):
        # Binding already established that the instance existed when requested.
        # A later drop makes an on-top request unusable, but an offscreen request
        # still records that retired instance and its old position for the return.
        if wid is None:
            return
        screen = self.home[wid]
        if screen == self.top():
            if self.can(wid):
                self.land(wid)
        elif screen not in self.dead:
            self.held[screen] = wid

    def feed(self, toks):
        kind = toks[0]
        if kind == "begin":
            assert len(toks) == 1 and len(self.frames) < 4, "invalid begin"
            self.frames.append({"tree": self.saved_tree(), "intents": []})
        elif kind in ("commit", "abort"):
            assert len(toks) == 1 and self.frames, "unmatched transaction close"
            frame = self.frames.pop()
            if kind == "abort":
                for field, value in frame["tree"].items():
                    setattr(self, field, value)
            elif self.frames:
                self.frames[-1]["intents"].extend(frame["intents"])
            else:
                self.check()
                for operation, target in frame["intents"]:
                    if operation == "want":
                        self.bound_want(target)
                    else:
                        self.event([operation])
        elif self.frames and (kind in self.KEYS or kind == "want"):
            target = None
            if kind == "want":
                target = self.names.get(toks[1])
                if target is not None and not self.live(target):
                    target = None
            self.frames[-1]["intents"].append((kind, target))
        else:
            assert not self.frames or kind not in ("push", "pop", "screen", "w"), \
                "screen changes and declarations are outside render transactions"
            super().feed(toks)


def solve(text):
    """The trail: external focus names after each event."""
    sim = BufferedSim()
    out = []
    for raw in text.splitlines():
        toks = raw.split()
        if toks:
            sim.feed(toks)
            if toks[0] not in ("screen", "w"):
                out.append(sim.labels[sim.focus] if sim.focus is not None else "none")
    assert not sim.frames, "unclosed render transaction"
    return out
