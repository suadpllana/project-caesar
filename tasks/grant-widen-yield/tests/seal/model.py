"""Independent model of the lock service, written from the frozen contract in STATE.md.

This file is the second implementation. It was written from the contract rather than from
`solution/`, and it is deliberately a different shape wherever the contract leaves a shape
free:

  * the cover a node needs is held as a count of the children's own effective modes, in a
    plain dict keyed (transaction, node), and the cover is derived by mapping that count -
    the reference keeps two integers already mapped to IS and IX;
  * subtrees are found by walking a per-transaction child map with an explicit queue and are
    ordered by an inverted depth key built here, against the reference's stack walk;
  * compatibility is decided from per-resource sets of holders grouped by mode, against the
    reference's per-mode counters;
  * the chain a take must reach is built by recursion from the resource outward, against the
    reference's iterative innermost-first pass;
  * claims are one dict of records carrying their own parked level, against the reference's
    pair of forward and backward indexes.

What is *not* independent, and is not claimed to be: both implementations key the claim sweep
on the level that refused each claim, and both keep the cover incrementally rather than
rescanning the children. Those are not free choices - the first is part of the contract
because a refused retake is not a quiet event, and the second is forced by the execution
limit. Everything the contract does leave free is settled differently here, which is what the
agreement over the graded population is evidence about.

`expect(lines)` takes a program as a list of lines and returns the trace and the closing
report exactly as the service must print them.
"""

MODES = ("IS", "IX", "S", "SIX", "X")

# Compatibility, written out as the pairs that CAN share a resource.
FRIEND = {
    "IS": {"IS", "IX", "S", "SIX"},
    "IX": {"IS", "IX"},
    "S": {"IS", "S"},
    "SIX": {"IS"},
    "X": set(),
}

# The lattice as two independent coordinates: how much of the resource the mode reads
# (0 intent, 1 all) and how much it writes (0 none, 1 intent, 2 all). The supremum is then
# the larger of each coordinate, and the cover above is IS exactly when nothing is written.
PAIR = {
    "IS": (0, 0),
    "IX": (0, 1),
    "S": (1, 0),
    "SIX": (1, 1),
    "X": (1, 2),
}
FROM_PAIR = dict((v, k) for k, v in PAIR.items())


def sup(a, b):
    if a is None:
        return b
    if b is None:
        return a
    x, y = PAIR[a]
    p, q = PAIR[b]
    return FROM_PAIR[(max(x, p), max(y, q))]


def cov(m):
    return "IX" if PAIR[m][1] else "IS"


def fits(a, b):
    return b in FRIEND[a]


def parent(res):
    cut = res.rfind(".")
    return res[:cut] if cut > 0 else None


def level(res):
    return res.count(".")


def spot(res):
    return tuple(int(p[1:]) for p in res.split("."))


def low_first(res):
    return (-level(res), spot(res))


class World(object):
    """Every rule of the contract, with no index the contract does not force."""

    def __init__(self):
        self.asked = {}      # (t, res) -> the mode the program or the widen rule wrote
        self.child = {}      # (t, res) -> {kid: kid's effective mode}
        self.live = {}       # (t, res) -> effective mode
        self.byres = {}      # res -> {mode: set of transactions}
        self.mine = {}       # t -> set of resources with a grant
        self.claim = {}      # (t, res) -> [mode, parked level or None]
        self.owned = {}      # t -> set of resources it has a claim on
        self.parked = {}     # level -> set of claims waiting on it
        self.atnode = {}     # res -> set of transactions with children there
        self.bumped = set()  # pairs whose child map changed
        self.moved = set()   # resources whose holders changed since the last sweep
        self.stirred = set() # the same, for the widen rule
        self.due = set()     # claims that may be tried in the next sweep
        self.age = {}
        self.order = []
        self.line = []

    # --- reading -----------------------------------------------------------------

    def eff(self, t, res):
        return self.live.get((t, res))

    def need(self, t, res):
        room = self.child.get((t, res))
        if not room:
            return None
        out = None
        for kid_mode in room.values():
            out = sup(out, cov(kid_mode))
        return out

    def blocked(self, t, res, goal):
        """The other transactions whose mode here cannot live beside goal."""
        seats = self.byres.get(res)
        if not seats:
            return []
        out = []
        for m, who in seats.items():
            if fits(m, goal):
                continue
            for u in who:
                if u != t:
                    out.append(u)
        return out

    def kids_of(self, t, res):
        return self.child.get((t, res), {})

    def subtree(self, t, top):
        """Every grant t holds at top or under it."""
        out = []
        queue = [top]
        while queue:
            here = queue.pop(0)
            if (t, here) in self.live:
                out.append(here)
            queue.extend(self.child.get((t, here), {}))
        out.sort(key=low_first)
        return out

    # --- writing -----------------------------------------------------------------

    def seat(self, res, t, was, now):
        book = self.byres.setdefault(res, {})
        if was is not None:
            book[was].discard(t)
            if not book[was]:
                del book[was]
        if now is not None:
            book.setdefault(now, set()).add(t)
        if not book:
            del self.byres[res]

    def place(self, t, res, val):
        """Move (t, res) to val and say so; then tell the level above."""
        was = self.live.get((t, res))
        if was == val:
            return
        self.moved.add(res)
        self.stirred.add(res)
        self.seat(res, t, was, val)
        if val is None:
            del self.live[(t, res)]
            self.mine[t].discard(res)
            self.line.append("free %s %s" % (t, res))
        else:
            self.live[(t, res)] = val
            self.mine.setdefault(t, set()).add(res)
            rising = was is None or sup(was, val) == val
            self.line.append("%s %s %s %s" % ("hold" if rising else "thin", t, res, val))
        up = parent(res)
        if up is not None:
            self.note(t, up, res, val)
            self.refresh(t, up)

    def note(self, t, up, kid, val):
        room = self.child.setdefault((t, up), {})
        if val is None:
            room.pop(kid, None)
        else:
            room[kid] = val
        seats = self.atnode.setdefault(up, set())
        if room:
            seats.add(t)
        else:
            seats.discard(t)
        self.bumped.add((t, up))

    def refresh(self, t, res):
        self.place(t, res, sup(self.asked.get((t, res)), self.need(t, res)))

    def unhook(self, t, res):
        """Remove one grant without a word and without touching what is above it."""
        was = self.live.pop((t, res), None)
        if was is not None:
            self.moved.add(res)
            self.stirred.add(res)
            self.seat(res, t, was, None)
            self.mine[t].discard(res)
        self.asked.pop((t, res), None)
        self.child.pop((t, res), None)
        seats = self.atnode.get(res)
        if seats is not None:
            seats.discard(t)
        up = parent(res)
        if up is not None:
            self.note(t, up, res, None)
        return was

    # --- claims ------------------------------------------------------------------

    def pin(self, key, at):
        rec = self.claim[key]
        if rec[1] is not None:
            self.parked.get(rec[1], set()).discard(key)
        rec[1] = at
        if at is not None:
            self.parked.setdefault(at, set()).add(key)

    def owe(self, t, res, m, at):
        key = (t, res)
        rec = self.claim.get(key)
        if rec is None:
            self.claim[key] = [m, None]
            self.owned.setdefault(t, set()).add(res)
            self.pin(key, at)
            self.due.add(key)
            return
        was = rec[0]
        rec[0] = sup(was, m)
        self.pin(key, at)
        if rec[0] != was:
            self.due.add(key)
        else:
            self.due.discard(key)

    def unowe(self, t, res):
        key = (t, res)
        if key in self.claim:
            self.pin(key, None)
            del self.claim[key]
            self.owned.get(t, set()).discard(res)
        self.due.discard(key)

    def wake(self):
        """A claim falls due again when the level that refused it moves."""
        if not self.moved:
            return
        for res in self.moved:
            for key in self.parked.get(res, ()):
                self.due.add(key)
        self.moved = set()

    # --- the take ----------------------------------------------------------------

    def aim(self, t, res, m):
        """The effective mode each level of the chain has to reach, by recursion outward."""
        here = sup(sup(self.asked.get((t, res)), m), self.need(t, res))
        plan = {res: here}
        up = parent(res)
        if up is not None:
            plan.update(self.aim_up(t, up, cov(here)))
        return plan

    def aim_up(self, t, res, from_below):
        here = sup(self.eff(t, res), from_below)
        plan = {res: here}
        up = parent(res)
        if up is not None:
            plan.update(self.aim_up(t, up, cov(here)))
        return plan

    def take(self, t, res, m, loud):
        plan = self.aim(t, res, m)
        walk = []
        node = res
        while node is not None:
            walk.append(node)
            node = parent(node)
        walk.reverse()
        for node in walk:
            goal = plan[node]
            if self.eff(t, node) == goal:
                continue
            foes = self.blocked(t, node, goal)
            if not foes:
                continue
            if any(self.age[u] < self.age[t] for u in foes):
                self.owe(t, res, m, node)
                if loud:
                    self.line.append("wait %s %s %s" % (t, res, m))
                return False
            for u in sorted(foes, key=lambda x: self.age[x]):
                self.yield_up(u, node)
        said = len(self.line)
        self.asked[(t, res)] = sup(self.asked.get((t, res)), m)
        self.refresh(t, res)
        self.line[said:] = list(reversed(self.line[said:]))
        self.unowe(t, res)
        return True

    def yield_up(self, u, top):
        """u gives up top and all of it; only an asked mode leaves a claim."""
        nodes = self.subtree(u, top)
        if not nodes:
            return
        for res in nodes:
            keep = self.asked.get((u, res))
            was = self.live.get((u, res))
            self.unhook(u, res)
            self.line.append("give %s %s %s" % (u, res, was))
            if keep is not None:
                self.owe(u, res, keep, None)
        up = parent(top)
        if up is not None:
            self.refresh(u, up)

    # --- the operations ----------------------------------------------------------

    def let_go(self, t, res):
        gone = set(self.subtree(t, res))
        stem = res + "."
        for where in self.owned.get(t, ()):
            if where == res or where.startswith(stem):
                gone.add(where)
        if not gone:
            return
        crown = self.eff(t, res)
        for node in sorted(gone, key=low_first):
            self.unhook(t, node)
            self.unowe(t, node)
            self.line.append("free %s %s" % (t, node))
        up = parent(res)
        if up is not None and crown is not None:
            self.refresh(t, up)

    def finish(self, t):
        gone = set(self.mine.get(t, ()))
        gone.update(self.owned.get(t, ()))
        for node in sorted(gone, key=low_first):
            self.line.append("free %s %s" % (t, node))
        for node in list(self.mine.get(t, ())):
            self.unhook(t, node)
        for res in list(self.owned.get(t, ())):
            self.unowe(t, res)
        self.mine.pop(t, None)
        self.owned.pop(t, None)
        self.line.append("shut %s" % t)

    # --- the sweep and the widen rule --------------------------------------------

    def sweep(self):
        self.wake()
        if not self.due:
            return
        batch = sorted(self.due, key=lambda c: (self.age[c[0]], level(c[1]), spot(c[1])))
        self.due = set()
        for t, res in batch:
            rec = self.claim.get((t, res))
            if rec is None:
                continue
            self.take(t, res, rec[0], False)

    def candidates(self, lim):
        out = set(self.bumped)
        self.bumped = set()
        for res in self.stirred:
            for u in self.atnode.get(res, ()):
                out.add((u, res))
        self.stirred = set()
        return [p for p in out if len(self.kids_of(p[0], p[1])) > lim]

    def widen(self, lim):
        pend = self.candidates(lim)
        while pend:
            pend.sort(key=lambda p: (-level(p[1]), self.age.get(p[0], 0), spot(p[1])))
            for t, node in pend:
                if t not in self.age:
                    continue
                room = self.kids_of(t, node)
                if len(room) <= lim:
                    continue
                goal = self.asked.get((t, node))
                for kid_mode in room.values():
                    goal = sup(goal, kid_mode)
                if any(True for _ in self.blocked(t, node, goal)):
                    continue
                count = len(room)
                doomed = []
                for kid in sorted(room, key=spot):
                    doomed.extend(self.subtree(t, kid))
                for res in sorted(set(doomed), key=low_first):
                    self.unhook(t, res)
                    self.line.append("free %s %s" % (t, res))
                before = self.eff(t, node)
                said = len(self.line)
                self.asked[(t, node)] = goal
                self.refresh(t, node)
                tail = self.line[said:]
                if tail and self.eff(t, node) != before:
                    tail.pop(0)
                self.line[said:] = ["wide %s %s %s %d" % (t, node, goal, count)] + tail
            pend = self.candidates(lim)

    # --- driving -----------------------------------------------------------------

    def play(self, rows):
        lim = 0
        for row in rows:
            bits = row.split()
            if not bits:
                continue
            head = bits[0]
            if head == "lim":
                lim = int(bits[1])
            elif head == "open":
                if bits[1] not in self.age:
                    self.age[bits[1]] = len(self.age)
                    self.order.append(bits[1])
            elif head == "take":
                self.take(bits[1], bits[2], bits[3], True)
            elif head == "drop":
                self.let_go(bits[1], bits[2])
            elif head == "shut":
                self.finish(bits[1])
            self.sweep()
            self.widen(lim)
        for t in self.order:
            for res in sorted(self.mine.get(t, ()), key=spot):
                self.line.append("own %s %s %s" % (t, res, self.eff(t, res)))
            held = [w for (u, w) in self.claim if u == t]
            for res in sorted(held, key=spot):
                self.line.append("due %s %s %s" % (t, res, self.claim[(t, res)][0]))
        return self.line


def expect(rows):
    return World().play(list(rows))
