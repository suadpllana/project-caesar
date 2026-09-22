"""What a blank can stand for, decided once per program.

A report row must hold under every filling, so the question for each blank is which of its
allowed values a filling could usefully give it. Three cases, settled here:

  free   the blank has more unused allowed values (values no row and no rule mentions) than
         there are blanks in the program, and no `X != c` can reach it. Every filling is then
         dominated by one that gives it a value nothing else holds: a positive rule can only
         gain matches when a value coincides with something, so the filling that minimises what
         is derived is the one where the blank equals only itself. It is treated as such.
  two    the same, but some `X != c` sits at a column the blank occupies. A filling can now
         kill a derivation by giving it c, so the cases are the compared constants it allows,
         plus one value nothing else holds. Any other value is dominated by that fresh one.
  all    fewer spare values than blanks: there may be no value it can take that nothing else
         holds, or not one per blank, so every allowed value is a case.

The count "more spare values than blanks" is what makes one fresh value per blank available
under every assignment of the others, with one to spare for showing that a row carrying a
fresh value is never certain. A single spare value shared by two blanks is not enough: the
filling that makes both spare makes them equal.
"""
import bisect

from rs.dom import Pick, Span
from rs.lex import Blank
from rs.rule import Var

FREE, TWO, ALL = "free", "two", "all"


class Star:
    """A value only its own blank holds: equal to nothing but itself."""

    __slots__ = ("of",)

    def __init__(self, of):
        self.of = of

    def __repr__(self):
        return "*" + self.of.name


def meet(a, b):
    """The values two allowed sets have in common, as a Span, a Pick or None when empty."""
    if isinstance(a, Span) and isinstance(b, Span):
        lo, hi = max(a.lo, b.lo), min(a.hi, b.hi)
        return Span(lo, hi) if lo <= hi else None
    if isinstance(a, Pick) and isinstance(b, Pick):
        keep = tuple(s for s in a.syms if s in b.syms)
        return Pick(keep) if keep else None
    return None


def size(d):
    return d.hi - d.lo + 1 if isinstance(d, Span) else len(d.syms)


def values(d):
    return range(d.lo, d.hi + 1) if isinstance(d, Span) else d.syms


class Kinds:
    """The class and the cases of every blank in a program."""

    def __init__(self, st):
        self.st = st
        ints, syms = set(), set()

        def note(v):
            if type(v) is int:
                ints.add(v)
            elif type(v) is str:
                syms.add(v)

        for t in st.tabs.values():
            for r in t.rows:
                for v in r:
                    note(v)
        for rl in st.rules:
            for at in rl.atoms:
                for a in at.args:
                    note(a)
            for _v, c in rl.nots:
                note(c)
        self.ints = sorted(ints)
        self.syms = syms

        # The allowed set of a blank is the meet over every column it sits in.
        allowed = {}
        for t in st.tabs.values():
            for r in t.rows:
                for col, v in zip(t.cols, r):
                    if isinstance(v, Blank):
                        allowed[v] = col if v not in allowed else meet(allowed[v], col)
        for b, d in allowed.items():
            if d is None:
                raise ValueError("no value is allowed for %s" % b.name)
        self.allowed = allowed

        # Which constants an inequality compares each column position with.
        near = {}
        for rl in st.rules:
            for v, c in rl.nots:
                for at in rl.atoms:
                    for i, a in enumerate(at.args):
                        if isinstance(a, Var) and a.name == v.name:
                            near.setdefault((at.tab, i), set()).add(c)
        reach = {}
        for t in st.tabs.values():
            for r in t.rows:
                for i, v in enumerate(r):
                    if isinstance(v, Blank) and (t.name, i) in near:
                        reach.setdefault(v, set()).update(near[(t.name, i)])

        n = len(allowed)
        self.kind, self.cases, self.caseset = {}, {}, {}
        for b, d in allowed.items():
            spare = size(d) - self.used(d)
            if spare >= n + 1:
                hit = sorted((c for c in reach.get(b, ()) if d.has(c)), key=order)
                self.kind[b] = TWO if hit else FREE
                cases = hit + [Star(b)]
            else:
                self.kind[b] = ALL
                cases = list(values(d))
            self.cases[b] = cases
            self.caseset[b] = frozenset(c for c in cases if not isinstance(c, Star))

    def used(self, d):
        """How many allowed values of d are mentioned anywhere in the program."""
        if isinstance(d, Span):
            return bisect.bisect_right(self.ints, d.hi) - bisect.bisect_left(self.ints, d.lo)
        return sum(1 for s in d.syms if s in self.syms)

    def free(self, b):
        return self.kind[b] == FREE

    def can_be(self, b, c):
        """Can a filling that matters give blank b the constant c?"""
        return c in self.caseset[b]

    def can_meet(self, a, b):
        """Can a filling that matters give two different blanks one value?"""
        if self.kind[a] == FREE or self.kind[b] == FREE:
            return False
        x, y = self.caseset[a], self.caseset[b]
        if len(x) > len(y):
            x, y = y, x
        return any(v in y for v in x)


def order(v):
    return (0, v, "") if type(v) is int else (1, 0, v)
