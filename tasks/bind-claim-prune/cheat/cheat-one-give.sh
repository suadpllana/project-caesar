#!/bin/bash
# one strong give per name, so nothing to fall back to (caught by shift-rebind)
set -euo pipefail

cat > /app/bind/hold.py <<'PYEOF'
class Keep:
    """The parts that are in, and who holds each claim key.

    Two things have to be separable here. A key held by a part that came out of a bundle can
    change hands; a key held by a part of a unit named in the input list cannot. Nothing else
    about a part is recorded, because a part's fate stops being a property of the part the
    moment a later unit can take its key away.
    """

    def __init__(self):
        self.loaded = set()
        self.parts = {}
        self.who = {}
        self.firm = set()


def load(keep, u, direct):
    """Bring a unit in. Returns the parts that entered and the parts that left.

    A unit named in the input list drops every bundle-held copy of the keys it carries first,
    so the copy that stands is out of the table before the copy that displaced it enters it,
    and two parts giving one name under one key never look like a second give.
    """
    out = []
    if direct:
        for p in u.parts:
            if p.key is None or p.key not in keep.who or p.key in keep.firm:
                continue
            out.append(keep.parts.pop(keep.who[p.key]))
            del keep.who[p.key]
    ins = []
    for p in u.parts:
        if p.key is not None:
            if p.key in keep.who:
                continue
            keep.who[p.key] = (p.unit, p.idx)
            if direct:
                keep.firm.add(p.key)
        keep.parts[(p.unit, p.idx)] = p
        ins.append(p)
    return ins, out
PYEOF

cat > /app/bind/want.py <<'PYEOF'
from bind import say


class Names:
    """What each name has been given by, and which names are still wanted.

    A name keeps every strong give it has collected, in arrival order, because the first of
    them can leave: one slot answers every program in which nothing is ever displaced and
    cannot say what the name falls back to. Wantedness is a count rather than a flag for the
    same reason - it moves down as well as up, so it cannot be latched.
    """

    def __init__(self):
        self.firm = {}
        self.soft = {}
        self.need = {}
        self.spare = {}
        self.want = set()


def enter(names, job, p):
    """A kept part's gives and uses arrive."""
    for nm, strong in p.gives:
        if strong:
            row = names.firm.setdefault(nm, [])
            if row:
                say.dup(job, nm, p.unit)
            else:
                row.append(p)
        else:
            names.soft.setdefault(nm, []).append(p)
        touch(names, nm)
    for nm, strong in p.uses:
        if strong:
            names.need[nm] = names.need.get(nm, 0) + 1
            touch(names, nm)


def leave(names, p):
    """A displaced part's gives and uses go back out. No report, and no second give."""
    for nm, strong in p.gives:
        row = names.firm.get(nm) if strong else names.soft.get(nm)
        if row:
            for i, q in enumerate(row):
                if q is p:
                    del row[i]
                    break
        touch(names, nm)
    for nm, strong in p.uses:
        if strong:
            names.need[nm] = names.need.get(nm, 0) - 1
            touch(names, nm)


def spares(names, u, order):
    for nm, size in u.spares:
        names.spare.setdefault(nm, []).append((size, order, u.name))
        touch(names, nm)


def touch(names, nm):
    if names.firm.get(nm):
        names.want.discard(nm)
    elif names.need.get(nm, 0) > 0 or nm in names.spare:
        names.want.add(nm)
    else:
        names.want.discard(nm)


def bind(names, nm):
    """The part a name stands on: the first strong give, else the first weak one."""
    row = names.firm.get(nm)
    if row:
        return row[0]
    row = names.soft.get(nm)
    if row:
        return row[0]
    return None
PYEOF

cat > /app/bind/pull.py <<'PYEOF'
from bind import say


class Scan:
    """One bundle, indexed once by name to the members that give it, in member order.

    A member gives a fixed set of names whatever the table happens to hold, so the index is
    built once and never rebuilt. What changes is which names are wanted, and a cursor per
    name walks past the members already taken, so the member a restart would have found is
    the smallest live position over the names wanted at that moment.
    """

    def __init__(self, job, name):
        self.name = name
        self.mem = job.bundles.get(name, ())
        self.taken = set()
        self.idx = {}
        for pos, who in enumerate(self.mem):
            u = job.units.get(who)
            if u is None:
                continue
            for p in u.parts:
                for nm, strong in p.gives:
                    if strong:
                        row = self.idx.get(nm)
                        if row is None:
                            self.idx[nm] = [pos]
                        elif row[-1] != pos:
                            row.append(pos)
        self.cur = {}


def pick(st, sc):
    """The position a restart from the first member would stop at, or None."""
    best = None
    for nm in st.names.want:
        row = sc.idx.get(nm)
        if not row:
            continue
        at = sc.cur.get(nm, 0)
        while at < len(row) and row[at] in sc.taken:
            at += 1
        sc.cur[nm] = at
        if at < len(row) and (best is None or row[at] < best):
            best = row[at]
    return best


def run(st, bundles):
    """Scan a bundle, or a group of them, until a whole pass takes nothing."""
    scans = [Scan(st.job, b) for b in bundles]
    while True:
        moved = False
        for sc in scans:
            while True:
                pos = pick(st, sc)
                if pos is None:
                    break
                sc.taken.add(pos)
                who = sc.mem[pos]
                if who in st.keep.loaded:
                    continue
                say.take(st.job, sc.name, who)
                st.load(who, False)
                moved = True
        if not moved:
            return
PYEOF

cat > /app/bind/place.py <<'PYEOF'
def run(st):
    """Names nothing gives, that some unit spared.

    Size is the largest spared, and the unit is the first in load order that spared it at that
    size, which is why the load order of every unit is carried rather than the declaration
    order. A give of either strength cancels the whole name, however late it arrived.
    """
    out = {}
    for nm, row in st.names.spare.items():
        if st.names.firm.get(nm) or st.names.soft.get(nm):
            continue
        best = None
        for size, order, who in row:
            if best is None or size > best[0] or (size == best[0] and order < best[1]):
                best = (size, order, who)
        out[nm] = (best[2], best[0])
    return out
PYEOF

cat > /app/bind/prune.py <<'PYEOF'
from bind import want


def run(st):
    """One walk out from the roots. Parts nothing reaches are out of the image.

    Asked per part this is a search each time; asked once from the roots it is a single walk,
    which is the whole difference at the size the link actually runs at. A weak use reaches
    nothing, so a part standing only under one is out even though its name still binds.
    """
    live = set()
    lit = set()
    stack = []
    for nm in st.job.roots:
        seed(st, nm, stack, live, lit)
    for spot in st.job.holds:
        if spot in st.keep.parts and spot not in live:
            live.add(spot)
            stack.append(st.keep.parts[spot])
    while stack:
        p = stack.pop()
        for nm, strong in p.uses:
            if strong:
                seed(st, nm, stack, live, lit)
    return live, lit


def seed(st, nm, stack, live, lit):
    p = want.bind(st.names, nm)
    if p is not None:
        spot = (p.unit, p.idx)
        if spot not in live:
            live.add(spot)
            stack.append(p)
    elif nm in st.set:
        lit.add(nm)


def count(st):
    total = 0
    for spot in st.live:
        total += st.keep.parts[spot].size
    for nm in st.lit:
        total += st.set[nm][1]
    return len(st.live) + len(st.lit), total
PYEOF

cat > /app/bind/wire.py <<'PYEOF'
from bind import hold, place, prune, pull, want


class Link:
    """One pass down the input list, then placement, then the prune.

    The take list and the table are different kinds of thing and are kept apart here: a take
    is printed when it happens and is never unsaid, while the table loses a part the moment a
    unit off the input list takes its key. Which is why the prune cannot run until the list is
    finished, and why the list cannot be settled by asking what the prune would keep.
    """

    def __init__(self, job):
        self.job = job
        self.keep = hold.Keep()
        self.names = want.Names()
        self.seen = 0
        self.set = {}
        self.live = set()
        self.lit = set()

    def load(self, uname, direct):
        u = self.job.units.get(uname)
        if u is None or uname in self.keep.loaded:
            return
        self.keep.loaded.add(uname)
        self.seen += 1
        ins, out = hold.load(self.keep, u, direct)
        for p in out:
            want.leave(self.names, p)
        for p in ins:
            want.enter(self.names, self.job, p)
        want.spares(self.names, u, self.seen)


def run(job, items):
    st = Link(job)
    job.link = st
    for kind, what in items:
        if kind == "u":
            st.load(what, True)
        elif kind == "b":
            pull.run(st, (what,))
        else:
            pull.run(st, what)
    st.set = place.run(st)
    st.live, st.lit = prune.run(st)


def at(job, nm):
    st = job.link
    if st is None:
        return None
    p = want.bind(st.names, nm)
    if p is not None:
        spot = (p.unit, p.idx)
        return spot if spot in st.live else None
    if nm in st.lit:
        who, size = st.set[nm]
        return ("spare", who, size)
    return None


def img(job):
    st = job.link
    if st is None:
        return (0, 0)
    return prune.count(st)
PYEOF

