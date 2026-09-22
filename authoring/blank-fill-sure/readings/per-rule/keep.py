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
    got = {q: set() for q in st.asks}
    for rl in st.rules:
        rows = {}
        for env, conds in join.derive(ways, kinds, rl):
            for row, c in heads(kinds, rl, env, conds):
                rows.setdefault(row, []).append(c)
        got[rl.ask] |= {row for row, conds in rows.items() if certain(kinds, conds)}
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
    return any(not falsifiable(kinds, g) for g in groups.values())


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
