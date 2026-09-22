#!/bin/bash
# a published partition is deleted with its keep like any other
set -euo pipefail

cat > /app/plan/keep.py <<'PYEOF'
"""Which partitions exist.

A partition exists once it has ended by now and for `keep` hours after that - while
end <= now < end + keep. A published partition is never deleted, so it exists as soon as it has
ended, whatever its keep.
"""
from plan.span import ends


def there(pp, name, i):
    if i < 0:
        return False
    end = ends(pp, name, i)
    if end > pp.now:
        return False
    return pp.now < end + pp.keep[name]
PYEOF

cat > /app/plan/reach.py <<'PYEOF'
"""What the correction reaches.

The corrected partition, and every partition of a step that has ended by now and reads a reached
partition by its declared reads - whether or not the partitions in between still exist, because
a partition that has expired still stood between its inputs and its readers when they were built.

Every read looks back in time, so nothing ending before the corrected partition can be reached:
the walk starts at the fix and inverts each read arithmetically rather than indexing every
partition from hour 0, which on two years of hourly history is what does not fit the clock.
"""
from plan.span import last


def fed_by(pp, src, i, name, kind, width):
    """The partitions of `name` whose `kind` read of `src` names partition i of src."""
    if kind == "same":
        return [i]
    if kind == "day":
        return [i // 24]
    if kind == "win":
        return range(i, i + width)
    if pp.grain[src] == pp.grain[name]:
        return [i + 1]
    if pp.grain[src] == "d":
        # an hourly step reads the day before its own: all 24 hours of the next day
        return range(24 * (i + 1), 24 * (i + 2))
    # a daily step reads the last hour of the day before its own
    return [(i + 1) // 24] if (i + 1) % 24 == 0 else []


def reach(pp):
    readers = {}
    for name in pp.names:
        for kind, src, width in pp.reads.get(name, ()):
            readers.setdefault(src, []).append((name, kind, width))
    got = {pp.fix}
    todo = [pp.fix]
    while todo:
        src, i = todo.pop()
        for name, kind, width in readers.get(src, ()):
            top = last(pp, name)
            for j in fed_by(pp, src, i, name, kind, width):
                if 0 <= j <= top and (name, j) not in got:
                    got.add((name, j))
                    todo.append((name, j))
    return got
PYEOF

cat > /app/plan/look.py <<'PYEOF'
"""How a computation reads its inputs.

Every computation - a rerun of a partition that exists, or a partition computed for the plan
because it no longer exists - reads what its step declares. Each partition it names is read from
storage if it exists; if it does not, it is computed for the plan from its own reads, unless it
belongs to a source, whose missing partitions nobody can bring back.

A daily step reading an hourly dataset by the day is the one exception. When the hourly dataset
has a roll-up and any hour of that day is missing, the roll-up's partition for the day is read in
place of all 24 hours - provided it exists and agrees with the corrected source once settled. A
published roll-up the correction reached does not agree, so the readers of the hours refuse it
while its own readers read it as published. The roll-up never stands in for its own computation.
"""
from plan.keep import there
from plan.span import takes


def rank_of(pp):
    """The order datasets are settled in within one end hour.

    Each dataset after the ones it reads, and each roll-up before every step that reads its hours
    by the day, because a reader has to know whether the roll-up agrees before it can use it.
    Declaration order breaks ties; it is not the order the plan prints in.
    """
    before = {name: set() for name in pp.names}
    for name in pp.names:
        for kind, src, _width in pp.reads.get(name, ()):
            if src != name:
                before[name].add(src)
            roll = pp.roll.get(src) if kind == "day" else None
            if roll is not None and roll != name:
                before[name].add(roll)
    rank, placed = {}, set()
    while len(placed) < len(pp.names):
        name = next(n for n in pp.names if n not in placed and before[n] <= placed)
        rank[name] = len(placed)
        placed.add(name)
    return rank


def named(pp, name, i):
    """Every partition the declared reads of (name, i) name, roll-ups aside."""
    for _kind, src, parts in takes(pp, name, i):
        for p in parts:
            yield src, p


def reads(pp, name, i, agrees):
    """What (name, i) reads: [(src, p, how)] with how in stored, temp, gone; and whether a
    roll-up stood in. `agrees(src, p)` answers for a partition that exists and was settled."""
    out, rolled = [], False
    for kind, src, parts in takes(pp, name, i):
        roll = pp.roll.get(src) if kind == "day" else None
        if roll is not None and roll != name \
                and not all(there(pp, src, h) for h in parts) \
                and there(pp, roll, i) and agrees(roll, i):
            out.append((roll, i, "stored"))
            rolled = True
            continue
        for p in parts:
            if there(pp, src, p):
                out.append((src, p, "stored"))
            elif src not in pp.reads:
                out.append((src, p, "gone"))
            else:
                out.append((src, p, "temp"))
    return out, rolled
PYEOF

cat > /app/plan/settle.py <<'PYEOF'
"""Settle every partition the plan could need, once, in time order - then decide the lines.

Two things make the plan something other than the downstream closure of the correction.

A partition is rerun only if something it reads, as it reads it, has changed. A published
partition is never rewritten and one that cannot be computed is left as it is, so neither passes
a change on, and a partition reached only through them is held - `same` - rather than rerun.

A partition that no longer exists is computed for the plan when a computation reads it, whether
or not the correction reached it; but it appears in the plan only if a rerun that is actually
made reads it, directly or through another computed partition. Whether the rerun is made depends
on whether what it reads changed, so everything is evaluated first and the lines come after.

The evaluation is iterative. The set of partitions to settle is the reached partitions that exist
plus every missing step partition their reads can lead to through other missing ones; it is
settled in order of end hour and then of rank_of, which puts everything a partition could read -
roll-ups included - before it. No partition is looked at twice, however many read it.
"""
from plan.keep import there
from plan.look import named, rank_of, reads
from plan.span import ends


class Rec:
    __slots__ = ("ok", "changed", "agrees", "rolled", "after", "temps", "line", "word")

    def __init__(self):
        self.ok, self.changed, self.agrees, self.rolled = True, False, True, False
        self.after, self.temps = [], []
        self.line, self.word = None, None


class Book:
    def __init__(self, pp, got):
        self.pp = pp
        self.got = got
        self.rank = rank_of(pp)
        self.rec = {}
        self.made = set()
        self.holds = []

    def flags(self, src, p):
        """(changed, agrees) of a partition that exists."""
        if (src, p) == self.pp.fix:
            return True, True
        r = self.rec.get((src, p))
        if r is None:
            return False, True          # not reached: untouched, and it agrees
        if r.line == "run":
            return True, r.agrees
        return False, False             # held: unchanged, and it no longer agrees

    def to_settle(self):
        pp = self.pp
        todo = [k for k in self.got if k[0] in pp.reads and there(pp, *k)]
        seen = set(todo)
        while todo:
            name, i = todo.pop()
            for src, p in named(pp, name, i):
                if (src, p) in seen or src not in pp.reads or there(pp, src, p):
                    continue
                seen.add((src, p))
                todo.append((src, p))
        return seen

    def compute(self, name, i):
        pp = self.pp
        r = Rec()
        here = there(pp, name, i)
        if here and (name, i) in pp.pins:
            r.line, r.word, r.agrees = "hold", "pinned", False
            return r
        entries, r.rolled = reads(pp, name, i, lambda s, p: self.flags(s, p)[1])
        for src, p, how in entries:
            if how == "gone":
                r.ok = False
            elif how == "temp":
                t = self.rec[(src, p)]
                if not t.ok:
                    r.ok = False
                    continue
                r.changed |= t.changed
                r.agrees &= t.agrees
                r.after.append((src, p))
                r.temps.append((src, p))
            else:
                changed, agrees = self.flags(src, p)
                r.changed |= changed
                r.agrees &= agrees
                if changed and (src, p) != pp.fix:
                    r.after.append((src, p))
        if not here:
            r.line = "temp" if r.ok else "fail"
        elif not r.ok:
            r.line, r.word = "hold", "lost"
        elif not r.changed:
            r.line, r.word = "hold", "same"
        else:
            r.line = "run"
            r.word = "part" if not r.agrees else ("sub" if r.rolled else "full")
        return r

    def settle(self):
        pp = self.pp
        for name, i in sorted(self.to_settle(),
                              key=lambda k: (ends(pp, *k), self.rank[k[0]], k[1])):
            self.rec[(name, i)] = self.compute(name, i)
        lined = [k for k in self.got if k[0] in pp.reads and there(pp, *k)]
        runs = [k for k in lined if self.rec[k].line == "run"]
        self.holds = [k for k in lined if self.rec[k].line == "hold"]
        self.made = set(runs)
        todo = list(runs)
        while todo:
            for t in self.rec[todo.pop()].temps:
                if t not in self.made:
                    self.made.add(t)
                    todo.append(t)
        return self


def settle(pp, got):
    return Book(pp, got).settle()
PYEOF

cat > /app/plan/order.py <<'PYEOF'
"""The order the plan runs in.

Every rerun and every computed partition comes after the lines of what it read - including a
roll-up it read in place of a day of hours, which is not a declared read and may be declared
after its reader. Of the lines free to go next, the one whose partition ends first goes, then
the one whose dataset is declared first. The holds follow, by end hour and then declaration.
"""
import heapq

from plan.span import ends


def order(pp, book):
    def key(k):
        return ends(pp, *k), pp.pos[k[0]]

    waiting = {k: {d for d in book.rec[k].after if d in book.made} for k in book.made}
    users = {}
    for k, before in waiting.items():
        for d in before:
            users.setdefault(d, []).append(k)
    free = [(key(k), k) for k, before in waiting.items() if not before]
    heapq.heapify(free)
    rows = []
    while free:
        _, k = heapq.heappop(free)
        r = book.rec[k]
        rows.append(("run", k[0], k[1], r.word) if r.line == "run" else ("temp", k[0], k[1]))
        for u in users.get(k, ()):
            waiting[u].discard(k)
            if not waiting[u]:
                heapq.heappush(free, (key(u), u))
    for k in sorted(book.holds, key=key):
        rows.append(("hold", k[0], k[1], book.rec[k].word))
    return rows
PYEOF
