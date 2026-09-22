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
