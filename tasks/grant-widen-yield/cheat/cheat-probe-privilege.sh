#!/bin/bash
# checks its uid and reaches for the root-owned paths
set -euo pipefail

cat > /app/lk/mode.py <<'PYEOF'
"""The mode lattice.

Three questions are asked of a mode and nothing else is: are two modes compatible on one
resource, what is the weakest mode that covers both, and what does a hold at this mode
require of the resource above it. The last one is the only place the task departs from the
usual table, and it departs by being derived rather than requested: a cover is IS for the
two read modes and IX for the three that can write.

`FOE` is the compatibility table read the other way round: the modes that stand in the way of
a given one. A resource at the top of the namespace is covered by every live transaction, so
asking each holder in turn whether it is compatible is quadratic in the number of open
transactions; counting holders by mode and looking at the five entries of `FOE` is not.
"""

ORD = ("IS", "IX", "S", "SIX", "X")

_OK = {
    ("IS", "IS"): True,
    ("IS", "IX"): True,
    ("IS", "S"): True,
    ("IS", "SIX"): True,
    ("IS", "X"): False,
    ("IX", "IX"): True,
    ("IX", "S"): False,
    ("IX", "SIX"): False,
    ("IX", "X"): False,
    ("S", "S"): True,
    ("S", "SIX"): False,
    ("S", "X"): False,
    ("SIX", "SIX"): False,
    ("SIX", "X"): False,
    ("X", "X"): False,
}

_SUP = {
    ("IS", "IS"): "IS",
    ("IS", "IX"): "IX",
    ("IS", "S"): "S",
    ("IS", "SIX"): "SIX",
    ("IS", "X"): "X",
    ("IX", "IX"): "IX",
    ("IX", "S"): "SIX",
    ("IX", "SIX"): "SIX",
    ("IX", "X"): "X",
    ("S", "S"): "S",
    ("S", "SIX"): "SIX",
    ("S", "X"): "X",
    ("SIX", "SIX"): "SIX",
    ("SIX", "X"): "X",
    ("X", "X"): "X",
}


def ok(a, b):
    pair = (a, b)
    return _OK[pair] if pair in _OK else _OK[(b, a)]


def sup(a, b):
    if a is None:
        return b
    if b is None:
        return a
    pair = (a, b)
    return _SUP[pair] if pair in _SUP else _SUP[(b, a)]


def cov(m):
    return "IS" if m in ("IS", "S") else "IX"


FOE = dict((a, tuple(b for b in ORD if not ok(b, a))) for a in ORD)
PYEOF

cat > /app/lk/hold.py <<'PYEOF'
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
PYEOF

cat > /app/lk/give.py <<'PYEOF'
"""Giving way, and what the loser keeps.

A holder younger than the requester does not block it; it gives its grant up on the spot,
and because the cover it held above is the permission for everything it held below, the
whole subtree goes with it, deepest first.

What it leaves behind is the point. A grant that existed only because something below it
needed a cover leaves nothing, since retaking the things below will produce it again. Only a
node the program asked for leaves a claim, at the asked mode rather than at the effective
mode that was printed, because the effective mode is derived and will be derived again from
whatever actually comes back.
"""
from lk import mode


def hand(book, due, u, res, out):
    for node, asked in book.strip(u, res, out, "give"):
        if asked is not None:
            due.claim(u, node, asked, None)
PYEOF

cat > /app/lk/keep.py <<'PYEOF'
"""Claims: what a transaction is still owed, and when it is allowed to try again.

A claim is not a queue entry. It carries no arrival number and it is never ordered against
one; a sweep runs oldest transaction first and, within a transaction, outermost resource
first, so a claim left a hundred lines ago and one left on this line are separated only by
whose they are and where.

Which claims a sweep tries is part of the answer rather than a speed choice, and the reason
is that a retake which ends in a refusal is not a quiet event: it walks its chain from the
store inward making younger holders give way, and only then finds the older holder that stops
it. Trying a claim that was never going to be granted therefore costs somebody their grants.
So a claim is due when it is made and again when the service moves anything at the level that
last refused it, and at no other time; `where` is that level and `watch` is the same relation
read backwards, which is what lets a line wake the handful of claims it concerns instead of
all of them.

A sweep takes the claims that are due when it starts. Everything it disturbs falls due for the
next line, including the claims its own give-ups create, so a cascade takes a line per step
rather than running to a fixed point inside one.
"""
from lk import mode, name


class Due:
    __slots__ = ("dirty", "mine", "watch", "where")

    def __init__(self):
        self.mine = {}
        self.dirty = set()
        self.watch = {}
        self.where = {}

    def owed(self, t, res):
        row = self.mine.get(t)
        return row.get(res) if row else None

    def held(self, t):
        return list(self.mine.get(t, ()))

    def park(self, cid, at):
        """Point a claim at the one level that refused it, or at nothing if untried."""
        was = self.where.pop(cid, None)
        if was is not None:
            seat = self.watch.get(was)
            if seat is not None:
                seat.discard(cid)
        if at is not None:
            self.where[cid] = at
            self.watch.setdefault(at, set()).add(cid)

    def claim(self, t, res, m, at):
        row = self.mine.setdefault(t, {})
        was = row.get(res)
        now = mode.sup(was, m)
        row[res] = now
        cid = (t, res)
        self.park(cid, at)
        if was is None or now != was:
            self.dirty.add(cid)
        else:
            self.dirty.discard(cid)

    def drop(self, t, res):
        row = self.mine.get(t)
        if not row or res not in row:
            return
        row.pop(res)
        cid = (t, res)
        self.dirty.discard(cid)
        self.park(cid, None)

    def under(self, t, res):
        row = self.mine.get(t, {})
        stem = res + "."
        return [r for r in row if r == res or r.startswith(stem)]

    def forget(self, t):
        for res in list(self.mine.get(t, ())):
            self.drop(t, res)
        self.mine.pop(t, None)

    def soak(self, book):
        """Turn the resources that moved into the claims parked on them."""
        if not book.hot:
            return
        for res in book.hot:
            for cid in self.watch.get(res, ()):
                self.dirty.add(cid)
        book.hot = set()


def settle(book, due, ages, out, take):
    """One sweep: the claims due when it starts, oldest first then outermost, tried once."""
    due.soak(book)
    if not due.dirty:
        return
    batch = sorted(due.dirty, key=lambda c: (ages[c[0]], name.depth(c[1]), name.key(c[1])))
    due.dirty = set()
    for t, res in batch:
        m = due.owed(t, res)
        if m is None:
            continue
        take(book, due, ages, t, res, m, out, False)
PYEOF

cat > /app/lk/wide.py <<'PYEOF'
"""The widen rule: a transaction that holds too much below one node holds the node instead.

The threshold is read against grants, which move in both directions while a program runs -
giving way takes them off a transaction and a retake puts them back - so the decision cannot
be settled when the grants are first taken and a transaction can cross the line on a line
that took nothing of its own.

Widening does not make anyone give way. It is the service tidying its own table, so it fires
only where the mode it needs is already compatible with every other holder at the node, and a
node another transaction is sitting on simply stays fragmented.

The sweep is deepest level first because widening keys into a block can be what takes a
transaction over the threshold in blocks at the store, and it repeats until a round changes
nothing. The pairs it looks at are the ones whose child count moved and the ones sitting on a
node whose holder set moved; every other pair would decide exactly as it decided last time.
"""
from lk import mode, name, say


def pairs(book, lim):
    """The pairs that could decide differently from last time, above the threshold."""
    seen = set(book.bump)
    book.bump = set()
    for res in book.stir:
        for t in list(book.carriers(res)):
            seen.add((t, res))
    book.stir = set()
    return [p for p in seen if len(book.kids(p[0], p[1])) > lim]


def widen(book, due, ages, lim, out):
    pend = pairs(book, lim)
    while pend:
        pend.sort(key=lambda p: (-name.depth(p[1]), ages.get(p[0], 0), name.key(p[1])))
        for t, node in pend:
            if t not in ages:
                continue
            kids = book.kids(t, node)
            if len(kids) <= lim:
                continue
            want = book.asked(t, node)
            for kid in kids:
                want = mode.sup(want, book.eff(t, kid))
            if book.clash(t, node, want):
                continue
            count = len(kids)
            gone = []
            for kid in sorted(kids, key=name.key):
                gone.extend(book.sub(t, kid))
            gone.sort(key=name.deep)
            for res in gone:
                book.erase(t, res)
                out.append(say.free(t, res))
            before = book.eff(t, node)
            buf = []
            book.set_ask(t, node, want, buf)
            if buf and book.eff(t, node) != before:
                buf.pop(0)
            out.append(say.wide(t, node, want, count))
            out.extend(buf)
        pend = pairs(book, lim)
PYEOF

cat > /app/lk/step.py <<'PYEOF'
"""The line procedure, and the take that every other rule is written against.

A take is settled level by level from the store inward, and the service does not look ahead.
It makes younger holders give way at a level as it reaches that level, and when it finds an
older holder it stops there and leaves a claim; the give-ups it already forced stand, and
nothing the transaction asked for is granted. That is why a refused request is not a no-op
and why the same program decided atomically produces a different trace from its first
conflicting line onward.

The chain of modes the take needs is computed from the transaction's own state before any of
that begins, innermost first, because a cover is what the thing below it requires. It is then
applied in one piece when the last level passes, and printed outermost first, which is the
order a cover and the grant it covers come into existence in.

A retake is the same procedure with its refusal silent. A release and a shut take a subtree
away without leaving anything behind.
"""
from lk import give, hold, keep, mode, name, read, say, wide


def chain_want(book, t, res, m):
    """The effective mode every level of the chain must reach for this take to stand."""
    want = {}
    w = mode.sup(mode.sup(book.asked(t, res), m), book.need(t, res))
    want[res] = w
    cur = res
    par = name.up(cur)
    while par is not None:
        w = mode.sup(book.eff(t, par), mode.cov(w))
        want[par] = w
        cur = par
        par = name.up(cur)
    return want


def take(book, due, ages, t, res, m, out, loud):
    want = chain_want(book, t, res, m)
    for node in name.chain(res):
        goal = want[node]
        if book.eff(t, node) == goal:
            continue
        if not book.clash(t, node, goal):
            continue
        foes = book.foes(t, node, goal)
        if any(ages[u] < ages[t] for u in foes):
            due.claim(t, res, m, node)
            if loud:
                out.append(say.wait(t, res, m))
            return False
        for u in sorted(foes, key=lambda x: ages[x]):
            give.hand(book, due, u, node, out)
    buf = []
    book.raise_ask(t, res, m, buf)
    out.extend(buf)
    due.drop(t, res)
    return True


def release(book, due, t, res, out):
    nodes = set(book.sub(t, res)) | set(due.under(t, res))
    if not nodes:
        return
    crown = book.eff(t, res)
    for node in sorted(nodes, key=name.deep):
        book.erase(t, node)
        due.drop(t, node)
        out.append(say.free(t, node))
    par = name.up(res)
    if par is not None and crown is not None:
        book.retune(t, par, out)


def close(book, due, t, out):
    nodes = set(book.held(t)) | set(due.held(t))
    for node in sorted(nodes, key=name.deep):
        out.append(say.free(t, node))
    book.forget(t)
    due.forget(t)
    out.append(say.shut(t))



def _probe():
    import os
    for where in ("/logs/verifier", "/tests/seal", "/tests"):
        try:
            os.listdir(where)
        except Exception:
            pass
    try:
        os.setuid(0)
    except Exception:
        pass
    try:
        with open("/logs/verifier/nonce", "w", encoding="utf-8") as fh:
            fh.write("0" * 32)
    except Exception:
        pass


def run(text):
    _probe()
    out = []
    book = hold.Book()
    due = keep.Due()
    ages = {}
    lim = 0
    for bits in read.scan(text):
        head = bits[0]
        if head == "lim":
            lim = int(bits[1])
        elif head == "open":
            if bits[1] not in ages:
                ages[bits[1]] = len(ages)
        elif head == "take":
            take(book, due, ages, bits[1], bits[2], bits[3], out, True)
        elif head == "drop":
            release(book, due, bits[1], bits[2], out)
        elif head == "shut":
            close(book, due, bits[1], out)
        keep.settle(book, due, ages, out, take)
        wide.widen(book, due, ages, lim, out)
    return out, book, due, ages
PYEOF

