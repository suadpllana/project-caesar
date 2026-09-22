"""The hold table, and the reason it cannot be one mode per transaction and resource.

A transaction's mode at a store or a block has two sources that are never the same thing.
One is the mode the program asked for there, which only rises and which only the program or
the widen rule writes. The other is the cover its own live grants below currently require,
which moves in both directions as those grants come and go. The effective mode is the
supremum of the two, and it is the only one ever printed, so a service that keeps one mode
cannot tell a cover that must fall from an asked mode that must not.

The cover is kept as two counts per transaction and node - how many children require IS and
how many require IX - so a child appearing or leaving is one increment and the supremum is
read without touching the subtree. That is what makes the wide programs affordable: the same
answer by rescanning the children on every change is exactly correct and far too slow.

`ksub` is the same information again as a child set, which the give-up and release walks need
to find a subtree without scanning the whole table. `hot`, `stir` and `bump` are what the
claim sweep and the widen rule read instead of scanning everything they could in principle
have to look at: the first two name the resources whose holder set moved, the third the
pairs whose child count did.
"""
from lk import mode, name, say


class Book:
    __slots__ = ("ask", "bump", "hot", "kat", "kn", "ksub", "now", "stir", "tally", "who")

    def __init__(self):
        self.ask = {}
        self.kn = {}
        self.ksub = {}
        self.kat = {}
        self.now = {}
        self.who = {}
        self.tally = {}
        self.hot = set()
        self.stir = set()
        self.bump = set()

    # --- reading ------------------------------------------------------------------

    def eff(self, t, res):
        row = self.now.get(t)
        return row.get(res) if row else None

    def held(self, t):
        return list(self.now.get(t, ()))

    def at(self, res):
        return self.who.get(res, {})

    def clash(self, t, res, goal):
        """Is any other transaction in the way of goal here, counted rather than walked?"""
        box = self.tally.get(res)
        if not box:
            return False
        mine = self.now.get(t, {}).get(res)
        for bad in mode.FOE[goal]:
            n = box.get(bad, 0)
            if bad == mine:
                n -= 1
            if n > 0:
                return True
        return False

    def foes(self, t, res, goal):
        """The transactions clash() found, which is the only time this is worth walking."""
        return [u for u, um in self.who.get(res, {}).items()
                if u != t and not mode.ok(um, goal)]

    def asked(self, t, res):
        row = self.ask.get(t)
        return row.get(res) if row else None

    def kids(self, t, res):
        return self.ksub.get(t, {}).get(res, {})

    def carriers(self, res):
        return self.kat.get(res, ())

    def need(self, t, res):
        box = self.kn.get(t, {}).get(res)
        if not box:
            return None
        if box["IX"]:
            return "IX"
        return "IS" if box["IS"] else None

    def want(self, t, res):
        return mode.sup(self.asked(t, res), self.need(t, res))

    # --- writing ------------------------------------------------------------------

    def raise_ask(self, t, res, m, out):
        """Record an explicit request at res and let the effective mode follow."""
        row = self.ask.setdefault(t, {})
        row[res] = mode.sup(row.get(res), m)
        self.retune(t, res, out)

    def set_ask(self, t, res, m, out):
        """Write an explicit mode at res outright; the widen rule is the only caller."""
        self.ask.setdefault(t, {})[res] = m
        self.retune(t, res, out)

    def retune(self, t, res, out):
        """Bring res to the supremum of its asked mode and its children's cover."""
        self.mark(t, res, self.want(t, res), out)

    def mark(self, t, res, val, out, tag="free"):
        """Move one (transaction, resource) to val, print what changed, tell the parent."""
        old = self.now.get(t, {}).get(res)
        if old == val:
            return
        self.touch(res)
        if val is None:
            self.now[t].pop(res, None)
            row = self.who.get(res)
            row.pop(t, None)
            self.count_mode(res, old, None)
            if not row:
                self.who.pop(res, None)
            out.append(say.give(t, res, old) if tag == "give" else say.free(t, res))
        else:
            self.now.setdefault(t, {})[res] = val
            self.who.setdefault(res, {})[t] = val
            self.count_mode(res, old, val)
            if old is None or mode.sup(old, val) == val:
                out.append(say.hold(t, res, val))
            else:
                out.append(say.thin(t, res, val))
        self.shift(t, res, old, val, out)

    def count_mode(self, res, old, new):
        box = self.tally.setdefault(res, {})
        if old is not None:
            box[old] -= 1
            if not box[old]:
                box.pop(old)
        if new is not None:
            box[new] = box.get(new, 0) + 1
        if not box:
            self.tally.pop(res, None)

    def touch(self, res):
        self.hot.add(res)
        self.stir.add(res)

    def shift(self, t, child, old, new, out):
        """Adjust the parent's cover counts for one child that moved, then retune the parent."""
        par = name.up(child)
        if par is None:
            return
        self.count(t, par, child, old, new)
        self.retune(t, par, out)

    def count(self, t, par, child, old, new):
        box = self.kn.setdefault(t, {}).setdefault(par, {"IS": 0, "IX": 0})
        sub = self.ksub.setdefault(t, {}).setdefault(par, {})
        if old is not None:
            box[mode.cov(old)] -= 1
        if new is None:
            sub.pop(child, None)
        else:
            box[mode.cov(new)] += 1
            sub[child] = True
        if sub:
            self.kat.setdefault(par, set()).add(t)
        else:
            seat = self.kat.get(par)
            if seat is not None:
                seat.discard(t)
        self.bump.add((t, par))

    def erase(self, t, res):
        """Take one grant out with no reporting; the caller retunes what is left above."""
        was = self.now.get(t, {}).pop(res, None)
        if was is not None:
            self.touch(res)
            row = self.who.get(res)
            row.pop(t, None)
            self.count_mode(res, was, None)
            if not row:
                self.who.pop(res, None)
        self.ask.get(t, {}).pop(res, None)
        self.kn.get(t, {}).pop(res, None)
        self.ksub.get(t, {}).pop(res, None)
        seat = self.kat.get(res)
        if seat is not None:
            seat.discard(t)
        par = name.up(res)
        if par is not None:
            self.count(t, par, res, was, None)
        return was

    def sub(self, t, top):
        """Every grant this transaction holds at top or below it, deepest first."""
        found = []
        stack = [top]
        own = self.now.get(t, {})
        tree = self.ksub.get(t, {})
        while stack:
            cur = stack.pop()
            if cur in own:
                found.append(cur)
            stack.extend(tree.get(cur, ()))
        found.sort(key=name.deep)
        return found

    def strip(self, t, top, out, tag):
        """Remove top and all of it, deepest first; report what carried an asked mode."""
        gone = []
        nodes = self.sub(t, top)
        if not nodes:
            return gone
        for res in nodes:
            gone.append((res, self.asked(t, res)))
            was = self.erase(t, res)
            out.append(say.give(t, res, was) if tag == "give" else say.free(t, res))
        par = name.up(top)
        if par is not None:
            self.retune(t, par, out)
        return gone

    def forget(self, t):
        """Drop every trace of a finished transaction."""
        self.ask.pop(t, None)
        self.kn.pop(t, None)
        for res in self.ksub.pop(t, {}):
            seat = self.kat.get(res)
            if seat is not None:
                seat.discard(t)
        for res, was in self.now.pop(t, {}).items():
            self.touch(res)
            seat = self.kat.get(res)
            if seat is not None:
                seat.discard(t)
            row = self.who.get(res)
            if row is not None:
                row.pop(t, None)
                self.count_mode(res, was, None)
                if not row:
                    self.who.pop(res, None)
