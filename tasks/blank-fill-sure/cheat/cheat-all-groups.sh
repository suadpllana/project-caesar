#!/bin/bash
# a row is certain only when every group of its conditions holds everywhere
set -euo pipefail

cat > /app/rs/cmp.py <<'PYEOF'
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
PYEOF

cat > /app/rs/join.py <<'PYEOF'
"""Every way a rule can derive a row, with the conditions under which it does.

A derivation matches each atom of the rule to a row, exactly as an ordinary join does, except
that a blank with cases (see cmp.py) may meet a constant or another such blank; the meeting is
then recorded as a condition instead of being decided. A free blank meets only itself. So a
derivation is a binding of the rule's variables plus a set of literals:

  ("=", b, c)    blank b takes the constant c
  ("~", a, b)    blanks a and b take one value (a sorts before b by name)
  ("!", b, c)    blank b does not take c, from an `X != c` of the rule

A derivation whose literals contradict each other is dropped as soon as they do.
"""
from rs.lex import Blank
from rs.rule import ANY, Var


def same(x, y):
    return type(x) is type(y) and x == y


class Ways:
    """Rows of one table by column value, and by the constants a blank there can take."""

    __slots__ = ("rows", "by", "can")

    def __init__(self, tab, kinds):
        self.rows = tab.rows
        self.by = [{} for _ in tab.cols]
        self.can = [{} for _ in tab.cols]
        for r in tab.rows:
            for i, v in enumerate(r):
                self.by[i].setdefault(v, []).append(r)
                if isinstance(v, Blank) and not kinds.free(v):
                    for c in kinds.caseset[v]:
                        self.can[i].setdefault(c, []).append(r)

    def meeting(self, i, x, kinds):
        """Rows whose column i can hold the term x."""
        if not isinstance(x, Blank):
            return self.by[i].get(x, []) + self.can[i].get(x, [])
        if kinds.free(x):
            return self.by[i].get(x, [])
        seen = {}
        for r in self.by[i].get(x, []):
            seen[id(r)] = r
        for c in kinds.caseset[x]:
            for r in self.by[i].get(c, []):
                seen[id(r)] = r
            for r in self.can[i].get(c, []):
                seen[id(r)] = r
        return list(seen.values())


def clash(conds, lit):
    """Does lit contradict a literal already held?"""
    op, a, b = lit
    for o, x, y in conds:
        if x is not a:
            continue
        if op == "=" and o == "=" and not same(y, b):
            return True
        if op == "=" and o == "!" and same(y, b):
            return True
        if op == "!" and o == "=" and same(y, b):
            return True
    return False


def add(conds, lit):
    if lit in conds:
        return conds
    if clash(conds, lit):
        return None
    return conds | {lit}


def meet(kinds, x, y, conds):
    """Match a row value x with a term y; the new conditions, or None when they cannot meet."""
    xb, yb = isinstance(x, Blank), isinstance(y, Blank)
    if not xb and not yb:
        return conds if same(x, y) else None
    if xb and yb:
        if x is y:
            return conds
        if not kinds.can_meet(x, y):
            return None
        a, b = (x, y) if x.name < y.name else (y, x)
        return add(conds, ("~", a, b))
    b, c = (x, y) if xb else (y, x)
    if kinds.free(b) or not kinds.can_be(b, c):
        return None
    return add(conds, ("=", b, c))


def derive(ways, kinds, rl):
    """All (binding, conditions) pairs of one rule."""
    out = []
    atoms = rl.atoms

    def walk(k, env, conds):
        if k == len(atoms):
            out.append((env, conds))
            return
        at = atoms[k]
        w = ways[at.tab]
        # Candidate rows come from the most selective bound column. A column bound to a
        # constant is cheap to look up; one bound to a blank with cases reaches every row that
        # holds one of its cases, so it is only looked up when nothing better is bound.
        best, later = None, []
        for i, a in enumerate(at.args):
            if a is ANY:
                continue
            if isinstance(a, Var):
                if a.name not in env:
                    continue
                term = env[a.name]
            else:
                term = a
            if isinstance(term, Blank) and not kinds.free(term):
                later.append((i, term))
                continue
            cand = w.meeting(i, term, kinds)
            if best is None or len(cand) < len(best):
                best = cand
        if best is None:
            for i, term in later:
                cand = w.meeting(i, term, kinds)
                if best is None or len(cand) < len(best):
                    best = cand
        if best is None:
            best = w.rows
        if not best:
            return
        for r in best:
            e2, c2 = env, conds
            for a, x in zip(at.args, r):
                if a is ANY:
                    continue
                if isinstance(a, Var):
                    if a.name in e2:
                        c2 = meet(kinds, x, e2[a.name], c2)
                    else:
                        if e2 is env:
                            e2 = dict(env)
                        e2[a.name] = x
                        continue
                else:
                    c2 = meet(kinds, x, a, c2)
                if c2 is None:
                    break
            else:
                walk(k + 1, e2, c2)

    walk(0, {}, frozenset())

    kept = []
    for env, conds in out:
        c2 = conds
        for v, c in rl.nots:
            x = env[v.name]
            if not isinstance(x, Blank):
                if same(x, c):
                    c2 = None
                    break
                continue
            if kinds.free(x) or not kinds.can_be(x, c):
                continue
            c2 = add(c2, ("!", x, c))
            if c2 is None:
                break
        if c2 is not None:
            kept.append((env, c2))
    return kept
PYEOF

cat > /app/rs/keep.py <<'PYEOF'
"""Which rows every filling returns.

A candidate row of constants collects the conditions of every derivation that produces it,
across all the rules of its query. It is returned under a filling exactly when one of those
conditions holds there, so it belongs in the report exactly when the disjunction of its
conditions holds under every assignment of the blanks with cases (the free ones are already
settled as values only they hold, see cmp.py).

Checking that disjunction over all its blanks at once is exact and exponential: a row with a
few hundred derivations, each on its own pair of blanks, has a few hundred independent groups.
Conditions on disjoint sets of blanks are independent, so the disjunction holds everywhere
exactly when the disjunction within one group does - otherwise a falsifying assignment for
each group, put together, falsifies them all. The check therefore splits the conditions into
groups that share no blank and searches each group for an assignment that falsifies all of its
conditions; a group with none makes the row certain.
"""
import itertools

from rs import cmp, join
from rs.lex import Blank


def report(st):
    kinds = cmp.Kinds(st)
    ways = {name: join.Ways(t, kinds) for name, t in st.tabs.items()}
    cand = {q: {} for q in st.asks}
    for rl in st.rules:
        rows = cand[rl.ask]
        for env, conds in join.derive(ways, kinds, rl):
            for row, c in heads(kinds, rl, env, conds):
                rows.setdefault(row, []).append(c)
    got = {}
    for q, rows in cand.items():
        got[q] = [row for row, conds in rows.items() if certain(kinds, conds)]
    return got


def heads(kinds, rl, env, conds):
    """The constant rows one derivation can produce, each with its full condition."""
    head = [env[v.name] for v in rl.head]
    blanks = []
    for x in head:
        if isinstance(x, Blank):
            if kinds.free(x):
                return
            if x not in blanks:
                blanks.append(x)
    if not blanks:
        yield tuple(head), conds
        return
    choices = []
    for b in blanks:
        fixed = [c for o, x, c in conds if o == "=" and x is b]
        if fixed:
            choices.append(fixed[:1])
        else:
            choices.append(sorted(kinds.caseset[b], key=cmp.order))
    for combo in itertools.product(*choices):
        pick = dict(zip(blanks, combo))
        c2 = conds
        for b, v in pick.items():
            c2 = join.add(c2, ("=", b, v))
            if c2 is None:
                break
        if c2 is None:
            continue
        yield tuple(pick[x] if isinstance(x, Blank) else x for x in head), c2


def blanks_of(cond):
    s = set()
    for _o, a, b in cond:
        s.add(a)
        if isinstance(b, Blank):
            s.add(b)
    return s


def certain(kinds, conds):
    if any(not c for c in conds):
        return True
    # Group the conditions by shared blanks.
    parent = {}

    def root(x):
        parent.setdefault(x, x)
        while parent[x] is not x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    sets = [blanks_of(c) for c in conds]
    for s in sets:
        it = iter(s)
        first = root(next(it))
        for b in it:
            r = root(b)
            if r is not first:
                parent[r] = first
    groups = {}
    for c, s in zip(conds, sets):
        groups.setdefault(root(next(iter(s))), []).append(c)
    return all(not falsifiable(kinds, g) for g in groups.values())


def holds(lit, asg):
    op, a, b = lit
    va = asg[a]
    if op == "~":
        return va is asg[b] if isinstance(va, cmp.Star) else join.same(va, asg[b])
    if op == "=":
        return join.same(va, b)
    return not join.same(va, b)


def falsifiable(kinds, conds):
    """Is there an assignment of this group's blanks under which no condition holds?"""
    order = sorted({b for c in conds for b in blanks_of(c)},
                   key=lambda b: -sum(1 for c in conds if b in blanks_of(c)))
    asg = {}

    def state(cond):
        known = True
        for lit in cond:
            op, a, b = lit
            if a not in asg or (op == "~" and b not in asg):
                known = False
                continue
            if not holds(lit, asg):
                return False
        return True if known else None

    def search(i):
        for c in conds:
            if state(c) is True:
                return False
        if i == len(order):
            return True
        b = order[i]
        for v in kinds.cases[b]:
            asg[b] = v
            if search(i + 1):
                return True
        del asg[b]
        return False

    return search(0)
PYEOF
