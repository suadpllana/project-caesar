"""Sealed model of the headless reader: what every page must print.

Written apart from the reference solution and deliberately shaped differently, so that a mistake
in one cannot hide in the other. The reference walks up the tree to answer "exposed?" and "which
region?"; this model caches both on every node and refreshes whole subtrees when something above
them changes. The reference keeps its waiting line in heaps with lazy deletion; this keeps exact
buckets per age. Both are checked against a third, naive reading that recomputes the page on
every tick, over thousands of generated pages.

THE MODEL
---------
Page. Element and text nodes with integer ids; node 0 is the page root and never moves, is never
dropped and never carries attributes. The elements carrying `aria-live` are fixed at load and it
only ever holds polite, assertive or off; later ticks may switch it between those values. Text is
one or more words separated by single spaces.

 1 Exposure. A node is exposed when it is attached and no element at or above it carries
   `hidden` (any value) or `aria-hidden` equal to `true`.
 2 Region. The nearest element at or above a node that carries aria-live; `off` counts and stops
   the search. A region voices while it is exposed and polite or assertive.
 3 Belief, per (region element, text node): the text, and the anchor - the node's parent when the
   entry was written. Written at load for everything exposed in a region, by a finishing
   utterance for every key it carried, and by absorption. What the reader will believe is the
   playing utterance's carried value where it carries the key, else the belief.
 4 Difference: the current value (text and parent of the node, when it is exposed in that
   region) against what the reader will believe, compared by presence and text only: an
   addition, a removal or a text change. A move inside a region is no difference.
 5 Absorption. A difference whose region does not voice, or whose kind is not named by the
   region element's own aria-relevant (tokens additions, removals, text, all; default additions
   text), is absorbed: belief takes the current value and the playing utterance stops carrying
   the key.
 6 Holds. A difference is held while an element on its hold path carries aria-busy equal to
   true: the node's parent up to the region element for an addition or text change; for a
   removal, the anchor up to the region element when the anchor is exposed in that region, else
   the region element alone.
 7 Age: the tick that first observed the difference, kept while it persists; a cut hands a
   carried key back with the age it had when it was carried.
 8 Selection whenever the reader is free: unheld assertive differences first, else polite;
   oldest first; ties to the lower text node id, then the lower region element id.
 9 Unit. From the start element (the node's parent; for a removal the anchor when it is exposed
   in the region, else none) up to the region element, the first element whose aria-atomic is
   true or false decides: true makes it the unit, false or none means no unit. A unit utterance
   is the unit's exposed text now and carries every unheld difference whose unit it is. Without
   a unit the utterance is the node's text, or `removed` and the believed text for a removal. An
   empty unit is believed at once and selection runs again.
10 An utterance of w words started at the end of tick t finishes at the end of tick t + w and
   teaches its carried values then. An unheld assertive difference cuts a playing polite
   utterance; assertive utterances are never cut.
11 For t = 1..T: apply the tick's ops; finish; observe; cut; select. A start prints
   `<t> <polite|assertive> <text>`, a cut prints `<t> cut`.
"""
import bisect

POL = ("polite", "assertive")
EVERY = frozenset(("additions", "removals", "text"))
USUAL = frozenset(("additions", "text"))


def parse(lines):
    last, ticks, cur = None, {}, None
    for raw in lines:
        p = raw.split()
        if not p:
            continue
        h = p[0]
        if h == "page":
            last = int(p[1])
        elif h.startswith("@"):
            cur = int(h[1:])
            ticks[cur] = []
        elif h == "add":
            pos = None if p[3] == "end" else int(p[3])
            ticks[cur].append(("add", int(p[1]), int(p[2]), pos, p[4],
                               p[5] if p[4] == "el" else " ".join(p[5:])))
        elif h == "move":
            ticks[cur].append(("move", int(p[1]), int(p[2]), None if p[3] == "end" else int(p[3])))
        elif h == "drop":
            ticks[cur].append(("drop", int(p[1])))
        elif h == "text":
            ticks[cur].append(("text", int(p[1]), " ".join(p[2:])))
        elif h == "set":
            ticks[cur].append(("set", int(p[1]), p[2], " ".join(p[3:])))
        elif h == "unset":
            ticks[cur].append(("unset", int(p[1]), p[2]))
        else:
            raise ValueError("unknown op: %s" % raw)
    return last, ticks


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


class Reader:
    def __init__(self):
        self.par = {0: None}
        self.kid = {0: []}
        self.att = {0: {}}
        self.txt = {}
        self.vis = {0: True}
        self.reg = {0: None}
        self.bel = {}
        self.fly = {}
        self.known = {}
        self.play = None
        self.dif = {}
        self.dcls = {}
        self.held = set()
        self.bucket = {"polite": {}, "assertive": {}}
        self.ages = {"polite": [], "assertive": []}
        self.in_reg = {}
        self.in_node = {}
        self.log = []

    # -- the page, with exposure and region cached per node -------------------------------

    def refresh(self, top):
        p = self.par[top]
        stack = [(top, self.vis[p], self.reg[p])]
        while stack:
            x, v, r = stack.pop()
            if x in self.txt:
                self.vis[x] = v
                self.reg[x] = r
                continue
            a = self.att[x]
            v = v and "hidden" not in a and a.get("aria-hidden") != "true"
            if "aria-live" in a:
                r = x
            self.vis[x] = v
            self.reg[x] = r
            for y in self.kid[x]:
                stack.append((y, v, r))

    def below(self, top):
        stack = [top]
        while stack:
            x = stack.pop()
            yield x
            stack.extend(self.kid.get(x, ()))

    def cur(self, k):
        r, n = k
        if self.vis.get(n) and self.reg.get(n) == r:
            return (self.txt[n], self.par[n])
        return None

    def voices(self, r):
        return self.vis.get(r, False) and self.att[r].get("aria-live") in POL

    def relevant(self, r):
        got = set()
        for tok in self.att[r].get("aria-relevant", "").split():
            if tok == "all":
                return EVERY
            if tok in EVERY:
                got.add(tok)
        return got or USUAL

    # -- belief ---------------------------------------------------------------------------

    def _know(self, k):
        r, n = k
        if k in self.bel or k in self.fly:
            self.known.setdefault(n, set()).add(r)
        else:
            s = self.known.get(n)
            if s:
                s.discard(r)

    def expect(self, k):
        if k in self.fly:
            return self.fly[k][0]
        return self.bel.get(k)

    def believe(self, k, v):
        if v is None:
            self.bel.pop(k, None)
        else:
            self.bel[k] = v
        self._know(k)

    # -- the waiting line -----------------------------------------------------------------

    def _unbucket(self, k):
        cls = self.dcls[k]
        age = self.dif[k]
        b = self.bucket[cls].get(age)
        if b is not None and k in b:
            b.discard(k)
            if not b:
                del self.bucket[cls][age]
                i = bisect.bisect_left(self.ages[cls], age)
                del self.ages[cls][i]

    def _bucket(self, k):
        cls = self.dcls[k]
        age = self.dif[k]
        b = self.bucket[cls].get(age)
        if b is None:
            b = self.bucket[cls][age] = set()
            bisect.insort(self.ages[cls], age)
        b.add(k)

    def unfile(self, k):
        if k not in self.dif:
            return
        if k not in self.held:
            self._unbucket(k)
        self.held.discard(k)
        r, n = k
        self.in_reg[r].discard(k)
        self.in_node[n].discard(r)
        del self.dif[k]
        del self.dcls[k]

    def file(self, k, age, cls, held):
        self.unfile(k)
        r, n = k
        self.dif[k] = age
        self.dcls[k] = cls
        self.in_reg.setdefault(r, set()).add(k)
        self.in_node.setdefault(n, set()).add(r)
        if held:
            self.held.add(k)
        else:
            self._bucket(k)

    def top(self, cls):
        ages = self.ages[cls]
        if not ages:
            return None
        return min(self.bucket[cls][ages[0]], key=lambda k: (k[1], k[0]))

    # -- where a difference sits -----------------------------------------------------------

    def start(self, k, c):
        r, _n = k
        if c is not None:
            return c[1]
        a = self.expect(k)[1]
        if self.vis.get(a) and self.reg.get(a) == r:
            return a
        return None

    def is_held(self, k, c):
        r = k[0]
        s = self.start(k, c)
        x = r if s is None else s
        while True:
            if self.att[x].get("aria-busy") == "true":
                return True
            if x == r:
                return False
            x = self.par[x]

    def unit(self, k, c):
        r = k[0]
        x = self.start(k, c)
        if x is None:
            return None
        while True:
            v = self.att[x].get("aria-atomic")
            if v == "true":
                return x
            if v == "false" or x == r:
                return None
            x = self.par[x]

    def text_of(self, u):
        out = []
        stack = [u]
        while stack:
            x = stack.pop()
            if x in self.txt:
                out.append(x)
                continue
            if not self.vis[x]:
                continue
            stack.extend(reversed(self.kid[x]))
        return out

    # -- observation ------------------------------------------------------------------------

    def settle(self, k, t, age=None):
        r = k[0]
        c = self.cur(k)
        e = self.expect(k)
        if not differs(c, e):
            self.unfile(k)
            return
        if not self.voices(r) or kind(c, e) not in self.relevant(r):
            self.fly.pop(k, None)
            self.believe(k, c)
            self.unfile(k)
            return
        if age is None:
            age = self.dif.get(k, t)
        self.file(k, age, self.att[r]["aria-live"], self.is_held(k, c))

    def rehold(self, k):
        if k not in self.dif:
            return
        h = self.is_held(k, self.cur(k))
        if h and k not in self.held:
            self._unbucket(k)
            self.held.add(k)
        elif not h and k in self.held:
            self.held.discard(k)
            self._bucket(k)

    def apply(self, op, touched):
        nodes, regs, rems, holds = touched
        h = op[0]
        if h == "add":
            _, n, p, pos, what, val = op
            self.par[n] = p
            ks = self.kid[p]
            ks.insert(len(ks) if pos is None else pos, n)
            if what == "el":
                self.kid[n] = []
                self.att[n] = {}
            else:
                self.txt[n] = val
                nodes.add(n)
            self.refresh(n)
        elif h in ("move", "drop"):
            n = op[1]
            q = self.par[n]
            if self.reg.get(q) is not None:
                rems.add(self.reg[q])
            self.kid[q].remove(n)
            if h == "move":
                p, pos = op[2], op[3]
                ks = self.kid[p]
                ks.insert(len(ks) if pos is None else pos, n)
                self.par[n] = p
                self.refresh(n)
            else:
                self.par[n] = None
            for x in self.below(n):
                if h == "drop":
                    self.vis[x] = False
                if x in self.txt:
                    nodes.add(x)
                elif "aria-live" in self.att[x]:
                    regs.add(x)
                    rems.add(x)
        elif h == "text":
            self.txt[op[1]] = op[2]
            nodes.add(op[1])
        else:
            e, name = op[1], op[2]
            if h == "set":
                self.att[e][name] = op[3]
            else:
                self.att[e].pop(name, None)
            if name in ("hidden", "aria-hidden"):
                q = self.par[e]
                if self.reg.get(q) is not None:
                    rems.add(self.reg[q])
                self.refresh(e)
                for x in self.below(e):
                    if x in self.txt:
                        nodes.add(x)
                    elif "aria-live" in self.att[x]:
                        regs.add(x)
                        rems.add(x)
            elif name == "aria-live":
                self.refresh(e)
                regs.add(e)
            elif name == "aria-relevant":
                if "aria-live" in self.att[e]:
                    regs.add(e)
            elif name == "aria-busy":
                if self.reg.get(e) is not None:
                    holds.add(self.reg[e])

    def observe(self, t, touched):
        nodes, regs, rems, holds = touched
        for n in nodes:
            ks = set()
            if self.vis.get(n) and self.reg.get(n) is not None:
                ks.add((self.reg[n], n))
            for r in self.known.get(n, ()):
                ks.add((r, n))
            for r in self.in_node.get(n, ()):
                ks.add((r, n))
            for k in ks:
                self.settle(k, t)
        for r in regs:
            for k in list(self.in_reg.get(r, ())):
                self.settle(k, t)
        for r in rems:
            for k in list(self.in_reg.get(r, ())):
                if self.cur(k) is None:
                    self.rehold(k)
        for r in holds:
            for k in list(self.in_reg.get(r, ())):
                self.rehold(k)

    # -- speech ------------------------------------------------------------------------------

    def load(self, ops):
        for op in ops:
            self.apply(op, (set(), set(), set(), set()))
        for n in self.txt:
            if self.vis.get(n) and self.reg.get(n) is not None:
                self.believe((self.reg[n], n), (self.txt[n], self.par[n]))

    def tick(self, t, ops):
        touched = (set(), set(), set(), set())
        for op in ops:
            self.apply(op, touched)
        if self.play is not None and self.play[1] == t:
            done, self.fly = self.fly, {}
            for k, (v, _a) in done.items():
                self.believe(k, v)
            self.play = None
        self.observe(t, touched)
        if self.play is not None and self.play[0] == "polite" and self.top("assertive"):
            self.log.append("%d cut" % t)
            back, self.fly = self.fly, {}
            self.play = None
            for k in back:
                self._know(k)
            for k, (_v, age) in back.items():
                self.settle(k, t, age=age)
        while self.play is None:
            k0 = self.top("assertive") or self.top("polite")
            if k0 is None:
                break
            c0 = self.cur(k0)
            u = self.unit(k0, c0)
            if u is None:
                took = [k0]
                words = c0[0] if c0 is not None else "removed " + self.expect(k0)[0]
            else:
                texts = self.text_of(u)
                words = " ".join(self.txt[x] for x in texts)
                r0 = k0[0]
                took = []
                for k in list(self.in_reg.get(r0, ())):
                    if k in self.held:
                        continue
                    if self.unit(k, self.cur(k)) == u:
                        took.append(k)
            carried = {k: (self.cur(k), self.dif[k]) for k in took}
            for k in took:
                self.unfile(k)
            if not words:
                for k, (v, _a) in carried.items():
                    self.believe(k, v)
                continue
            cls = self.att[k0[0]]["aria-live"]
            self.fly = carried
            for k in carried:
                self._know(k)
            self.play = (cls, t + len(words.split(" ")))
            self.log.append("%d %s %s" % (t, cls, words))


def expect(lines):
    if isinstance(lines, str):
        lines = lines.splitlines()
    last, ticks = parse(lines)
    rd = Reader()
    rd.load(ticks[0])
    for t in range(1, last + 1):
        rd.tick(t, ticks.get(t, ()))
    return rd.log
