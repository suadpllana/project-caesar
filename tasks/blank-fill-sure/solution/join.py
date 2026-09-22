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
        best = None
        for i, a in enumerate(at.args):
            if a is ANY:
                continue
            if isinstance(a, Var):
                if a.name not in env:
                    continue
                cand = w.meeting(i, env[a.name], kinds)
            else:
                cand = w.meeting(i, a, kinds)
            if best is None or len(cand) < len(best):
                best = cand
                if not best:
                    return
        if best is None:
            best = w.rows
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
